import aws_cdk as cdk
from my_cdk_app.ec2_alb_stack import Ec2AlbStack

app = cdk.App()
Ec2AlbStack(app, "Ec2AlbStack")
app.synth()
