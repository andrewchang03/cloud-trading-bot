from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_efs as efs,
    aws_ec2 as ec2
)
from constructs import Construct


class TradingBotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, 'TradingBotVPC', max_azs=2)

        fs = efs.FileSystem(self, 'TradingBotFileSystem',
                            vpc=vpc,
                            removal_policy=RemovalPolicy.DESTROY)

        access_point = fs.add_access_point('HuggingFaceAccessPoint',
                                           create_acl=efs.Acl(
                                               owner_gid='1001', owner_uid='1001', permissions='750'),
                                           path="/export/models",
                                           posix_user=efs.PosixUser(gid="1001", uid="1001"))

        check_sentiment_docker_lambda = _lambda.DockerImageFunction(self, 'CheckSentimentDockerLambda',
                                                                    code=_lambda.DockerImageCode.from_image_asset(
                                                                        '../../algo-bot/src/sentiment'),
                                                                    timeout=Duration.seconds(
                                                                        899),
                                                                    memory_size=1024,
                                                                    vpc=vpc,
                                                                    filesystem=_lambda.FileSystem.from_efs_access_point(
                                                                        access_point, '/mnt/hf_models_cache'),
                                                                    environment={
                                                                        "TRANSFORMERS_CACHE": "/mnt/hf_models_cache"},
                                                                    )

        get_news_data_docker_lambda = _lambda.DockerImageFunction(self, 'GetNewsDataDockerLambda',
                                                                  code=_lambda.DockerImageCode.from_image_asset(
                                                                        '../../algo-bot/src/newsdata'),
                                                                  # Default is only 3 seconds
                                                                  timeout=Duration.seconds(
                                                                      120),
                                                                  memory_size=256  # If your docker code is pretty complex
                                                                  )

        strategy_docker_lambda = _lambda.DockerImageFunction(self, 'StrategyDockerLambda',
                                                             code=_lambda.DockerImageCode.from_image_asset(
                                                                 '../../algo-bot/src/strategy'),
                                                             # Default is only 3 seconds
                                                             timeout=Duration.seconds(
                                                                 120),
                                                             memory_size=256  # If your docker code is pretty complex
                                                             )

        calc_profit_lambda = _lambda.DockerImageFunction(self, 'CalcProfitLambda',
                                                         code=_lambda.DockerImageCode.from_image_asset(
                                                             '../../algo-bot/src/calc_profit'),
                                                         # Default is only 3 seconds
                                                         timeout=Duration.seconds(
                                                             120),
                                                         memory_size=256  # If your docker code is pretty complex
                                                         )

        sentiment_data = dynamodb.Table(self, "SentimentData",
                                        partition_key=dynamodb.Attribute(
                                            name="company", type=dynamodb.AttributeType.STRING),
                                        sort_key=dynamodb.Attribute(
                                            name="article", type=dynamodb.AttributeType.STRING),
                                        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST)

        current_options = dynamodb.Table(self, "CurrentOptions",
                                         partition_key=dynamodb.Attribute(
                                             name="contract_id", type=dynamodb.AttributeType.STRING),
                                         billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST)
        daily_earnings = dynamodb.Table(self, "DailyEarnings",
                                        partition_key=dynamodb.Attribute(
                                            name="activityId", type=dynamodb.AttributeType.STRING),
                                        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST)

        current_options.add_global_secondary_index(
            partition_key=dynamodb.Attribute(
                name='expiry', type=dynamodb.AttributeType.STRING),
            index_name='expiry_index')

        # check_sentiment lambda writes to sentiment_data ddb
        sentiment_data.grant_write_data(check_sentiment_docker_lambda)

        # strategy lambda queries sentiment_data ddb, writes/querys current_options ddb
        current_options.grant_read_write_data(strategy_docker_lambda)
        daily_earnings.grant_read_write_data(strategy_docker_lambda)
        sentiment_data.grant_read_data(strategy_docker_lambda)

        # calc_profit needs
        current_options.grant_read_write_data(calc_profit_lambda)
        daily_earnings.grant_read_write_data(calc_profit_lambda)
