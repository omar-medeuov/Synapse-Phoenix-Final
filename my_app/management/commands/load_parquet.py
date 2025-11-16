from django.core.management.base import BaseCommand
from django.utils import timezone
import warnings

import polars as pl
import pyarrow.parquet as pq

from my_app.models import Transaction


class Command(BaseCommand):
    help = "Load data from parquet into DB"

    def handle(self, *args, **options):
        # Suppress timezone warnings temporarily
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='django.db.models.fields')
        
        import time
        start_time = time.time()
        
        # Open parquet file to get metadata
        parquet_file = pq.ParquetFile("example_dataset.parquet")
        total_rows = parquet_file.metadata.num_rows
        self.stdout.write(f'Total rows to process: {total_rows:,}')
        self.stdout.write(f'Estimated time: ~{total_rows / 1000 / 60:.1f} minutes (rough estimate)')
        
        total_loaded = 0
        batch_objs = []
        db_batch_size = 5_000
        
        # Use PyArrow's batch iterator to read in small batches
        # This avoids loading entire row groups into memory
        batch_size = 1_000  # Read 1000 rows per batch from parquet
        
        def make_timezone_aware(dt):
            """Convert naive datetime to timezone-aware if needed"""
            if dt is None:
                return None
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt
        
        # Iterate through row groups
        for rg_idx in range(parquet_file.num_row_groups):
            self.stdout.write(f'Processing row group {rg_idx + 1} / {parquet_file.num_row_groups}')
            
            # Use iter_batches to read in smaller chunks from the row group
            try:
                row_group_reader = parquet_file.iter_batches(
                    batch_size=batch_size,
                    row_groups=[rg_idx]
                )
                
                batch_count = 0
                for arrow_batch in row_group_reader:
                    # Convert Arrow batch directly to Polars DataFrame
                    chunk_df = pl.from_arrow(arrow_batch)
                    
                    # Convert chunk to list of Transaction objects
                    for row in chunk_df.iter_rows(named=True):
                        # Fix timezone issue for datetime field
                        timestamp = row["transaction_timestamp"]
                        if timestamp is not None and timezone.is_naive(timestamp):
                            timestamp = timezone.make_aware(timestamp)
                        
                        batch_objs.append(
                            Transaction(
                                transaction_id=row["transaction_id"],
                                transaction_timestamp=timestamp,
                                card_id=row["card_id"],
                                expiry_date=row.get("expiry_date"),
                                issuer_bank_name=row.get("issuer_bank_name"),
                                merchant_id=row.get("merchant_id"),
                                merchant_mcc=row.get("merchant_mcc"),
                                mcc_category=row.get("mcc_category"),
                                merchant_city=row.get("merchant_city"),
                                transaction_type=row.get("transaction_type"),
                                transaction_amount_kzt=row.get("transaction_amount_kzt"),
                                original_amount=row.get("original_amount"),
                                transaction_currency=row.get("transaction_currency"),
                                acquirer_country_iso=row.get("acquirer_country_iso"),
                                pos_entry_mode=row.get("pos_entry_mode"),
                                wallet_type=row.get("wallet_type"),
                                index_level_0=row.get("__index_level_0__"),
                            )
                        )
                        
                        # Bulk create when batch is full
                        if len(batch_objs) >= db_batch_size:
                            Transaction.objects.bulk_create(batch_objs, batch_size=db_batch_size, ignore_conflicts=True)
                            total_loaded += len(batch_objs)
                            batch_objs = []
                    
                    batch_count += 1
                    # Show progress more frequently
                    if batch_count % 5 == 0:
                        elapsed = time.time() - start_time
                        progress = (total_loaded / total_rows) * 100 if total_rows > 0 else 0
                        if total_loaded > 0:
                            rate = total_loaded / elapsed  # rows per second
                            remaining = (total_rows - total_loaded) / rate if rate > 0 else 0
                            self.stdout.write(
                                f'Batch {batch_count} | Loaded: {total_loaded:,}/{total_rows:,} ({progress:.1f}%) | '
                                f'Rate: {rate:.0f} rows/sec | ETA: {remaining/60:.1f} min'
                            )
                        else:
                            self.stdout.write(
                                f'Batch {batch_count} | Loaded: {total_loaded:,}/{total_rows:,} ({progress:.1f}%)'
                            )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error processing row group {rg_idx}: {str(e)}')
                )
                # Try alternative method: read row group in smaller slices
                try:
                    # Fallback: use Polars lazy evaluation with smaller slices
                    lf = pl.scan_parquet("example_dataset.parquet")
                    row_group_size = parquet_file.metadata.row_group(rg_idx).num_rows
                    slice_size = 500  # Very small slices
                    
                    for slice_offset in range(0, row_group_size, slice_size):
                        # Calculate global offset
                        global_offset = sum(
                            parquet_file.metadata.row_group(i).num_rows 
                            for i in range(rg_idx)
                        ) + slice_offset
                        
                        chunk_df = lf.slice(global_offset, slice_size).collect(streaming=True)
                        
                        for row in chunk_df.iter_rows(named=True):
                            # Fix timezone issue for datetime field
                            timestamp = row["transaction_timestamp"]
                            if timestamp is not None and timezone.is_naive(timestamp):
                                timestamp = timezone.make_aware(timestamp)
                            
                            batch_objs.append(
                                Transaction(
                                    transaction_id=row["transaction_id"],
                                    transaction_timestamp=timestamp,
                                    card_id=row["card_id"],
                                    expiry_date=row.get("expiry_date"),
                                    issuer_bank_name=row.get("issuer_bank_name"),
                                    merchant_id=row.get("merchant_id"),
                                    merchant_mcc=row.get("merchant_mcc"),
                                    mcc_category=row.get("mcc_category"),
                                    merchant_city=row.get("merchant_city"),
                                    transaction_type=row.get("transaction_type"),
                                    transaction_amount_kzt=row.get("transaction_amount_kzt"),
                                    original_amount=row.get("original_amount"),
                                    transaction_currency=row.get("transaction_currency"),
                                    acquirer_country_iso=row.get("acquirer_country_iso"),
                                    pos_entry_mode=row.get("pos_entry_mode"),
                                    wallet_type=row.get("wallet_type"),
                                    index_level_0=row.get("__index_level_0__"),
                                )
                            )
                            
                            if len(batch_objs) >= db_batch_size:
                                Transaction.objects.bulk_create(batch_objs, batch_size=db_batch_size, ignore_conflicts=True)
                                total_loaded += len(batch_objs)
                                batch_objs = []
                except Exception as e2:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to process row group {rg_idx} with fallback method: {str(e2)}')
                    )
                    continue
        
        # Insert any remaining objects
        if batch_objs:
            Transaction.objects.bulk_create(batch_objs, batch_size=db_batch_size, ignore_conflicts=True)
            total_loaded += len(batch_objs)
        
        elapsed_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {total_loaded:,} transactions into the database in {elapsed_time/60:.1f} minutes '
                f'({elapsed_time:.1f} seconds)'
            )
        )

