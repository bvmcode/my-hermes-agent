############################
# Networking lookups
############################

data "aws_vpc" "default" {
  count   = var.subnet_id == null ? 1 : 0
  default = true
}

data "aws_subnets" "default" {
  count = var.subnet_id == null ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

data "aws_subnet" "selected" {
  id = coalesce(var.subnet_id, try(sort(data.aws_subnets.default[0].ids)[0], null))
}

############################
# AMI: latest Ubuntu 24.04 LTS (Canonical)
############################

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

############################
# Security group: dashboard port, optional SSH
############################

resource "aws_security_group" "hermes" {
  name_prefix = "${var.name}-"
  description = "Hermes Agent instance"
  vpc_id      = data.aws_subnet.selected.vpc_id

  egress {
    description = "All outbound (LLM APIs, messaging platforms, package installs)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = length(var.dashboard_allowed_cidrs) > 0 ? [1] : []
    content {
      description = "Hermes dashboard"
      from_port   = var.dashboard_port
      to_port     = var.dashboard_port
      protocol    = "tcp"
      cidr_blocks = var.dashboard_allowed_cidrs
    }
  }

  dynamic "ingress" {
    for_each = length(var.ssh_allowed_cidrs) > 0 ? [1] : []
    content {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.ssh_allowed_cidrs
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = { Name = var.name }
}

############################
# IAM: SSM access, plus create RDS databases and query them
############################

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# Create RDS databases, then create tables and read/write rows.
# Table and row changes are SQL, run as the master user (password in the
# RDS-managed secret) or through the RDS Data API. No delete or modify.
data "aws_iam_policy_document" "rds" {
  statement {
    sid = "CreateRdsDatabases"
    actions = [
      "rds:CreateDBInstance",
      "rds:CreateDBCluster",
      "rds:CreateDBSubnetGroup",
      "rds:AddTagsToResource",
    ]
    resources = ["*"]
  }

  statement {
    sid = "DescribeRds"
    actions = [
      "rds:DescribeDBInstances",
      "rds:DescribeDBClusters",
      "rds:DescribeDBSubnetGroups",
      "rds:DescribeDBEngineVersions",
      "rds:DescribeOrderableDBInstanceOptions",
      "rds:ListTagsForResource",
    ]
    resources = ["*"]
  }

  statement {
    sid = "RunSql"
    actions = [
      "rds-data:ExecuteStatement",
      "rds-data:BatchExecuteStatement",
      "rds-data:BeginTransaction",
      "rds-data:CommitTransaction",
      "rds-data:RollbackTransaction",
    ]
    resources = [
      "arn:aws:rds:${var.region}:${data.aws_caller_identity.current.account_id}:cluster:*",
    ]
  }

  statement {
    sid = "ReadRdsCredentials"
    actions = [
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:rds!*",
    ]
  }

  statement {
    sid = "DecryptRdsSecret"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${var.region}.amazonaws.com"]
    }
  }

  statement {
    sid = "CreateDatabaseSecurityGroup"
    actions = [
      "ec2:CreateSecurityGroup",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:CreateTags",
    ]
    resources = [
      "arn:aws:ec2:${var.region}:${data.aws_caller_identity.current.account_id}:security-group/*",
      "arn:aws:ec2:${var.region}:${data.aws_caller_identity.current.account_id}:vpc/${data.aws_subnet.selected.vpc_id}",
    ]
  }

  statement {
    sid    = "DenyInstanceSecurityGroupChanges"
    effect = "Deny"
    actions = [
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupEgress",
    ]
    resources = [aws_security_group.hermes.arn]
  }

  statement {
    sid = "DescribeNetworking"
    actions = [
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
      "ec2:DescribeVpcs",
    ]
    resources = ["*"]
  }

  statement {
    sid     = "CreateRdsServiceLinkedRole"
    actions = ["iam:CreateServiceLinkedRole"]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/rds.amazonaws.com/AWSServiceRoleForRDS",
    ]

    condition {
      test     = "StringEquals"
      variable = "iam:AWSServiceName"
      values   = ["rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "hermes" {
  name_prefix        = "${var.name}-"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.hermes.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "rds" {
  name   = "rds-create-and-data"
  role   = aws_iam_role.hermes.id
  policy = data.aws_iam_policy_document.rds.json
}

resource "aws_iam_instance_profile" "hermes" {
  name_prefix = "${var.name}-"
  role        = aws_iam_role.hermes.name
}

############################
# EC2 instance
############################

resource "aws_instance" "hermes" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnet.selected.id
  vpc_security_group_ids = [aws_security_group.hermes.id]
  iam_instance_profile   = aws_iam_instance_profile.hermes.name
  key_name               = var.ssh_key_name

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    install_url    = var.hermes_install_url
    dashboard_port = var.dashboard_port
  })
  user_data_replace_on_change = true

  metadata_options {
    http_tokens   = "required" # IMDSv2 only
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size_gb
    encrypted   = true
  }

  tags = { Name = var.name }
}
