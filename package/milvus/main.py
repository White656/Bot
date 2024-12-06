from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, has_collection


class MilvusClient:
    def __init__(self, host: str = "localhost", port: str = "19530"):
        """
        Initializes a new instance of MilvusClient.

        Args:
            host (str): The host address of the Milvus server.
            port (str): The port number of the Milvus server.
        """
        self.host = host
        self.port = port
        self.connection_alias = "default"
        self._connect()

    def _connect(self):
        """
        Establish a connection to the Milvus server.
        """
        connections.connect(alias=self.connection_alias, host=self.host, port=self.port)

    def create_collection(self, collection_name: str, dim: int, metric_type: str = "COSINE"):
        """
        Create a collection in Milvus if it does not already exist.

        Args:
            collection_name (str): The name of the collection.
            dim (int): The dimensionality of the vectors.
            metric_type (str): The distance metric type (COSINE, L2, etc.).
        """
        # Проверка, существует ли коллекция
        if not has_collection(collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
            ]
            schema = CollectionSchema(fields, description=f"Collection for {collection_name}")
            collection = Collection(name=collection_name, schema=schema)

            # Создаем индекс для коллекции
            index_params = {
                "index_type": "HNSW",
                "metric_type": metric_type,
                "params": {"M": 16, "efConstruction": 200},
            }
            collection.create_index(field_name="vector", index_params=index_params)
            print(f"Коллекция '{collection_name}' успешно создана.")
        else:
            print(f"Коллекция '{collection_name}' уже существует.")

    def insert_vectors(self, collection_name: str, vectors: list[list[float]]):
        """
        Insert vectors into a collection with auto-incremented IDs.

        Args:
            collection_name (str): The name of the collection.
            vectors (list[list[float]]): List of vectors to insert.
        """
        collection = Collection(collection_name)

        # Поскольку IDs генерируются автоматически, передаем только векторы
        data = [vectors]
        collection.insert(data)

        print(f"Inserted {len(vectors)} vectors into collection '{collection_name}'")

    def search_vectors(self, collection_name: str, query_vector: list[float], limit: int = 5):
        """
        Search for similar vectors in a collection.

        Args:
            collection_name (str): The name of the collection.
            query_vector (list[float]): The vector to search for.
            limit (int): The number of top results to return.

        Returns:
            list[dict]: List of search results with IDs and distances.
        """
        collection = Collection(collection_name)
        collection.load()
        search_params = {"metric_type": "COSINE", "params": {"ef": 50}}
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=limit,
            output_fields=["id"],
        )
        output = [
            {"id": hit.id, "distance": hit.distance} for hits in results for hit in hits
        ]
        print(f"Search completed. Found {len(output)} results.")
        return output

    def delete_vector(self, collection_name: str, vector_id: int):
        """
        Delete a vector from a collection by its ID.

        Args:
            collection_name (str): The name of the collection.
            vector_id (int): The ID of the vector to delete.
        """
        collection = Collection(collection_name)
        expr = f"id == {vector_id}"
        collection.delete(expr)
        print(f"Vector with ID {vector_id} deleted from collection '{collection_name}'")

    def drop_collection(self, collection_name: str):
        """
        Drop a collection from Milvus.

        Args:
            collection_name (str): The name of the collection.
        """
        collection = Collection(collection_name)
        collection.drop()
        print(f"Collection '{collection_name}' dropped.")

    def get_all_vectors(self, collection_name: str):
        """
        Получает все эмбеддинги и их ID из указанной коллекции.

        Args:
            collection_name (str): Имя коллекции.

        Returns:
            list[dict]: Список всех векторов с их ID.
        """
        collection = Collection(collection_name)
        collection.load()

        # Запрашиваем все данные из коллекции
        results = collection.query(expr="id != 0", output_fields=["id", "vector"], liimit=100)

        print(f"Получено {len(results)} записей из коллекции '{collection_name}'")
        return results
