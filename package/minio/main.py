from fontTools.mtiLib import bucketizeRules
from minio import Minio


class MinioClient(object):

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        '''
        Initializes a new instance of a class with the necessary credentials and
        endpoint configuration to perform operations.

        Args:
            endpoint (AnyUrl): The base URL for the endpoint to connect to.
            access_key (str): The public key required for authentication.
            secret_key (str): The private key used for secure access.

        '''
        self.__secret_key = secret_key
        self._access_key = access_key
        self.uri = endpoint
        self.__client: Minio | None = None

    @property
    def connection(self) -> Minio:
        """
        Returns a Minio client connection. This property checks if the client
        is initialized, if not, it creates a new Minio client using the provided URI,
        access key, and secret key, and then returns the client. This ensures a
        consistent and efficient way to manage the Minio client connection.

        Attributes:
            __client (Minio): The Minio client used for connecting to the storage.
            uri (str): The URI of the Minio server.
            _access_key (str): The access key for authentication with the Minio server.
            __secret_key (str): The secret key for authentication with the Minio server.

        Returns:
            Minio: The Minio client connection.
        """
        if self.__client is None:
            self.__client = Minio(self.uri,
                                  access_key=self._access_key,
                                  secret_key=self.__secret_key,
                                  )
        return self.__client

    def get_or_create_bucket(self, bucket_name: str) -> (bool, str):
        """
        Manages operations related to bucket creation and management in a storage
        service.

        Attributes:
            connection: Represents the connection to the storage service.
        """
        bucket = self.connection.bucket_exists(bucket_name)
        if bucket is None:
            self.connection.make_bucket(bucket_name=bucket_name)
        return bucket, bucket_name

    def upload_file_to_bucket(self, bucket_name: str, file_io, object_name: str) -> None:
        """
        Uploads a file from io format to a specified bucket in the storage service.

        Args:
            bucket_name (str): The name of the bucket where the file will be stored.
            file_io (IO): The file-like object to upload.
            object_name (str): The name of the object in the bucket.
        """
        _, bucket = self.get_or_create_bucket(bucket_name)
        self.connection.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=file_io,
            length=-1,  # Specify the file length, or for unknown length specify -1 for stream
            part_size=10 * 1024 * 1024  # You can adjust the part size
        )

    def get_file_from_bucket(self, bucket_name: str, object_name: str) -> (bytes, str):
        """
        Downloads a file from a specified bucket and returns its content and URL.

        Args:
            bucket_name (str): The name of the bucket from which to download the file.
            object_name (str): The name of the object to download.

        Returns:
            Tuple: A tuple containing the file content (as bytes) and the URL for accessing the file.
        """
        # Getting the object from the bucket
        response = self.connection.get_object(bucket_name, object_name)
        try:
            # Reading the data from the response
            file_data = response.read()
        finally:
            # Make sure to close the response to release the connection
            response.close()
            response.release_conn()

        # Constructing a URL for the object
        url = self.connection.presigned_get_object(bucket_name, object_name)

        return file_data, url
