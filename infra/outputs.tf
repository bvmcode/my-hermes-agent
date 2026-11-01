output "instance_id" {
  value = aws_instance.hermes.id
}

output "public_ip" {
  value = aws_instance.hermes.public_ip
}

output "dashboard_url" {
  description = "Hermes Desktop remote gateway URL."
  value       = "http://${aws_instance.hermes.public_ip}:${var.dashboard_port}"
}

output "connect_ssm" {
  description = "Open a shell via SSM Session Manager (needs the AWS CLI + session-manager-plugin locally)."
  value       = "aws ssm start-session --region ${var.region} --target ${aws_instance.hermes.id} --document-name AWS-StartInteractiveCommand --parameters command=\"sudo -iu ubuntu\""
}

output "connect_ssh" {
  description = "SSH command, if you enabled a key pair and SSH CIDRs."
  value       = var.ssh_key_name == null ? "SSH not enabled - use connect_ssm" : "ssh ubuntu@${aws_instance.hermes.public_ip}"
}

# Sourceable env file. INSTANCE_ID is what `make login` reads.
resource "local_file" "outputs" {
  filename        = "${path.module}/outputs.txt"
  file_permission = "0600"
  content = join("", [
    "export INSTANCE_ID=${aws_instance.hermes.id}\n",
    "export instance_id=${aws_instance.hermes.id}\n",
    "export public_ip=${aws_instance.hermes.public_ip}\n",
    "export dashboard_url=http://${aws_instance.hermes.public_ip}:${var.dashboard_port}\n",
    "export connect_ssm='aws ssm start-session --region ${var.region} --target ${aws_instance.hermes.id} --document-name AWS-StartInteractiveCommand --parameters command=\"sudo -iu ubuntu\"'\n",
    "export connect_ssh='${var.ssh_key_name == null ? "SSH not enabled - use connect_ssm" : "ssh ubuntu@${aws_instance.hermes.public_ip}"}'\n",
  ])
}
