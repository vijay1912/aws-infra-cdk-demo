import aws_cdk as cdk
from my_cdk_app.ec2_nlb_stack import Ec2NlbStack

app = cdk.App()
Ec2NlbStack(app, "Ec2NlbStack")
app.synth()
