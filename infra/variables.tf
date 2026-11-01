variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "my-hermes-agent"
}

variable "instance_type" {
  description = "EC2 instance type. Hermes bundles Node.js and a headless Chromium for browser tools, so 4 GB RAM (t3.medium) is a sensible floor. More RAM is only needed if Ollama loads a model on this instance."
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 30
}

variable "subnet_id" {
  description = "Subnet to launch into. Leave null to use the first subnet of the default VPC."
  type        = string
  default     = null
}

variable "ssh_key_name" {
  description = "Existing EC2 key pair name for SSH. Leave null to rely on SSM Session Manager only (recommended)."
  type        = string
  default     = null
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to SSH in (e.g. [\"203.0.113.4/32\"]). Empty list = no inbound SSH."
  type        = list(string)
  default     = []
}

variable "dashboard_port" {
  description = "TCP port the Hermes dashboard listens on."
  type        = number
  default     = 9119
}

variable "dashboard_allowed_cidrs" {
  description = "CIDRs allowed to reach the Hermes dashboard. Empty list closes the port. Narrow this to your own IP; the dashboard also requires the username and password generated on the instance."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "hermes_install_url" {
  description = "URL of the official Hermes Agent installer script."
  type        = string
  default     = "https://hermes-agent.nousresearch.com/install.sh"
}
