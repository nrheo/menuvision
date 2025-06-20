import boto3

s3 = boto3.client("s3")
textract = boto3.client("textract")
comprehend = boto3.client("comprehend")

def lambda_handler(event, context):
    try:
        bucket = event["bucket"]
        key = event["key"]

        # 1. Read PDF from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        file_bytes = obj["Body"].read()

        # 2. Extract text using Textract
        response = textract.detect_document_text(Document={'Bytes': file_bytes})
        lines = [block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"]
        extracted_text = "\n".join(lines)

        # 3. Detect dominant language
        lang_response = comprehend.detect_dominant_language(Text=extracted_text[:5000])
        lang_code = lang_response["Languages"][0]["LanguageCode"]

        # ✅ Return plain JSON (not wrapped in "body")
        return {
            "language": lang_code,
            "text": extracted_text
        }

    except Exception as e:
        # Optional: for debugging in Step Functions
        return {
            "error": str(e)
        }
