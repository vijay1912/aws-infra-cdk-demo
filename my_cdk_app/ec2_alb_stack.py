from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    CfnOutput
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

        # Auto Scaling Group (using key_name for now)
        asg = autoscaling.AutoScalingGroup(
            self, "MyASG",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            min_capacity=1,
            max_capacity=3,
            security_group=sg,
            key_name="my-keypair"  # fallback property, no feature flag needed
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

        # Listener with default target group (attach ASG here)
        listener = alb.add_listener("Listener", port=80, default_action=elbv2.ListenerAction.forward(
            [asg]
        ))

        # Health check configuration
        listener.add_targets("AppFleet",
            port=80,
            targets=[asg],
            health_check=elbv2.HealthCheck(
                path="/",
                port="80",
                protocol=elbv2.Protocol.HTTP,
                healthy_threshold_count=2,
                unhealthy_threshold_count=2,
                interval=Duration.seconds(30)
            )
        )

        # Output ALB DNS
        CfnOutput(self, "AlbDnsName", value=alb.load_balancer_dns_name)
