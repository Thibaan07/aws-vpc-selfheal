output "instance_public_ip" {
  description = "Public IP of the web server"
  value       = aws_instance.web.public_ip
}

output "ssh_command" {
  description = "Command to SSH in"
  value       = "ssh -i ~/.ssh/tf-key ec2-user@${aws_instance.web.public_ip}"
}