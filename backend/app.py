from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import uuid
import json
from botocore.exceptions import BotoCoreError, ClientError

app = Flask(__name__)

# ✅ Proper global CORS setup — allows requests from your frontend
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}})

REGION = "us-east-1"
BUCKET_NAME = "Your Bucket Name"
STEP_FUNCTION_ARN = "Your Step Function ARN"
IMAGE_LAMBDA_NAME = "generateImageLambda"

s3_client = boto3.client("s3", region_name=REGION)
sfn_client = boto3.client("stepfunctions", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

@app.route('/get-upload-url', methods=['POST'])
def get_upload_url():
    try:
        data = request.json
        file_name = data.get('fileName', 'default.pdf')
        object_name = f"uploads/{uuid.uuid4()}_{file_name}"

        print(f"[DEBUG] Generating pre-signed URL for: {object_name}")

        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': object_name,
                'ContentType': 'application/pdf'
            },
            ExpiresIn=300
        )

        print(f"[DEBUG] Generated URL: {presigned_url}")

        return jsonify({
            'uploadUrl': presigned_url,
            'objectKey': object_name
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to generate URL: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/start-step-function', methods=['POST'])
def start_step_function():
    try:
        data = request.json
        object_key = data['objectKey']

        response = sfn_client.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps({'bucket': BUCKET_NAME, 'key': object_key})
        )

        return jsonify({'executionArn': response['executionArn']})

    except (BotoCoreError, ClientError) as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-status', methods=['GET'])
def check_status():
    try:
        execution_arn = request.args.get('executionArn')
        response = sfn_client.describe_execution(executionArn=execution_arn)

        if response['status'] == 'SUCCEEDED':
            output = json.loads(response['output'])  # String → Dict
            return jsonify({'status': 'SUCCEEDED', 'result': output})
        else:
            return jsonify({'status': response['status']})
    except Exception as e:
        print(f"[ERROR] Failed to check execution status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.json
        menu_item = data['item']

        # ✅ Rename 'item' to 'prompt'
        response = lambda_client.invoke(
            FunctionName=IMAGE_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps({'prompt': menu_item}).encode()
        )

        result = json.load(response['Payload'])
        print("[DEBUG] Lambda image result:", result)
        return jsonify(result)

    except (BotoCoreError, ClientError) as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=3000, debug=True)
