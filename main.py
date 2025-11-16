import polars as pl



# Lazy scan – doesn't read immediately

lf = pl.scan_parquet("example_dataset.parquet")



result = (

    lf

    .select(["card_id", "transaction_amount_kzt"])

    .filter(pl.col("card_id") > 100)

    .collect()  # actual read happens here

    

)

print(result)