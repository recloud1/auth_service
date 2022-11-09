
def user_partition(target, connection, **kwargs) -> None:
    """Create partitions by users registration year."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS "registered_2021"
        PARTITION OF "users"
        FOR VALUES FROM ('2021-01-01') TO ('2021-12-31');
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS "registered_2022"
        PARTITION OF "users"
        FOR VALUES FROM ('2022-01-01') TO ('2022-12-31');
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS "registered_2023"
        PARTITION OF "users"
        FOR VALUES FROM ('2023-01-01') TO ('2023-12-31');
        """
    )


def social_accounts_partition(target, connection, **kwargs) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS "yandex" 
        PARTITION OF "user_social_accounts" 
        FOR VALUES IN ('yandex')
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS "mail" 
        PARTITION OF "user_social_accounts" 
        FOR VALUES IN ('mail')
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS "vk" 
        PARTITION OF "user_social_accounts" 
        FOR VALUES IN ('vk')
        """
    )
