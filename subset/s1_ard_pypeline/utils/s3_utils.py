import boto3

from s1_ard_pypeline import get_config


class S3Utils:
    """
    A simple interface around the S3 access commands.
    Only provides the tools that we need.
    """

    def __init__(self):
        access = get_config("S3", "access_key")
        secret = get_config("S3", "secret_key")
        endpoint_url = get_config("S3", "endpoint_url")

        session = boto3.Session(
            access,
            secret,
            get_config("S3", "region"),
        )
        self.s3 = session.resource('s3', endpoint_url=endpoint_url)
        self.client = session.client('s3', endpoint_url=endpoint_url)
        self.bucket = self.s3.Bucket(get_config("S3", "bucket"))
        self.gb = 1024 ** 3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            endpoint_url=endpoint_url
        )
        # Ensure that multipart uploads only happen if the size of a transfer is larger than S3's size limit for
        # non multipart uploads, which is 5 GB. we copy using multipart at anything over 4gb
        self.transfer_config = boto3.s3.transfer.TransferConfig(multipart_threshold=2 * self.gb, max_concurrency=10,
                                                                multipart_chunksize=2 * self.gb, use_threads=True)

    def count(self):
        """
        Count the number of objects in the bucket.

        :return: The number of objects in the bucket
        """
        return sum(1 for _ in self.bucket.objects.all())

    def list_files(self, prefix):
        """
        Create and return a list of all files in the bucket.
        
        :param: Prefix to search for, primarily a path but it's just a string match.
        :return: List of strings.
        """

        filenames = []
        for obj in self.bucket.objects.filter(Prefix=prefix):
            filenames.append(obj.key)

        return filenames

    def fetch_file(self, path, destination):
        """
        Download a file from S3 and put it in the destination

        :param path: location in S3 to get the file from.
        :param destination: where on the local file system to put the file
        :return: None
        """
        self.bucket.download_file(path, destination)

    def put_file(self, source, destination):
        """
        put a file into S3 from the local file system.

        :param source: a path to a file on the local file system
        :param destination: where in S3 to put the file.
        :return: None
        """
        transfer = boto3.s3.transfer.S3Transfer(client=self.s3_client, config=self.transfer_config)
        transfer.upload_file(source, self.bucket.name, destination)
