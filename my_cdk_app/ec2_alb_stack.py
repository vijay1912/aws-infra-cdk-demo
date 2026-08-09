from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    Duration
)
from constructs import Construct

class Ec2AlbStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)

        # Security Group
        sg = ec2.SecurityGroup(
            self, "MySecurityGroup",
            vpc=vpc,
            description="Allow SSH and HTTP",
            allow_all_outbound=True
        )
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")

        # Auto Scaling Group
        asg = autoscaling.AutoScalingGroup(
            self, "MyASG",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            min_capacity=1,
            max_capacity=3,
            security_group=sg,
            key_pair=ec2.KeyPair.from_key_pair_name(self, "MyKeyPair", "my-keypair")
        )

        # User Data: install Apache
        asg.add_user_data(
            "sudo yum update -y",
            "sudo yum install -y httpd",
            "sudo systemctl start httpd",
            "sudo systemctl enable httpd",
            "echo '<h1>Hello from Auto Scaling EC2 behind ALB!</h1>' | sudo tee /var/www/html/index.html"
        )

        # Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self, "MyALB",
            vpc=vpc,
            internet_facing=True,
            security_group=sg
        )

        # Listener
        listener = alb.add_listener("Listener", port=80)

        # Attach ASG to ALB
        listener
