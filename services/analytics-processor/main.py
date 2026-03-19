import base64
import json
from google.cloud import bigquery, firestore

# Initialize clients
bq_client = bigquery.Client()
db = firestore.Client()

def process_telemetry(event, context):
    """Triggered by Pub/Sub; writes to BQ and Firestore independently"""
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)
    helmet_id = data.get('helmet_id', 'unknown')
    
    # 1. Real-Time Update (Firestore)
    try:
        db.collection('live_telemetry').document(helmet_id).set({
            **data,
            "last_updated": firestore.SERVER_TIMESTAMP
        })
        print(f"✅ MAP UPDATE: Synced {helmet_id} to Firestore")
    except Exception as e:
        print(f"❌ FIRESTORE ERROR: {e}")

    # 2. Historical Archive (BigQuery)
    try:
        table_id = f"{bq_client.project}.omnistream_analytics.helmet_telemetry_raw"
        # THE FIX: Tell BigQuery to drop 'trace_id' instead of crashing
        errors = bq_client.insert_rows_json(table_id, [data], ignore_unknown_values=True)
        if errors:
            print(f"❌ BQ REJECTED DATA: {errors}")
        else:
            print(f"✅ BQ ARCHIVE: Saved {helmet_id}")
    except Exception as e:
        print(f"❌ BQ EXCEPTION: {e}")