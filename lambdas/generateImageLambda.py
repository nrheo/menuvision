import boto3
import json
import base64
import uuid
import os
import random

# 🔧 EDIT THIS: Your S3 bucket name
BUCKET_NAME = "S3 bucket"

# 🔧 EDIT THIS: Folder inside the bucket to store generated images
FOLDER = "images"

# 🔧 You can also replace model_id with a different Bedrock model if needed
MODEL_ID = "stability.stable-diffusion-xl-v1"

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    try:
        prompt = event.get("prompt", "")
        style = event.get("style", "photorealistic")

        if not prompt:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'prompt'"})
            }

        # 🎨 Prompt templates by style
        prompt_templates = [
            f"high-quality photo of {prompt}, styled for Instagram food bloggers",
            f"beautifully lit, close-up of {prompt}, vibrant colors, DSLR look",
            f"top-down shot of {prompt} on rustic wood with moody lighting",
            f"{prompt} on ceramic plate, bokeh background, natural light",
            f"{prompt}, styled for a trendy food magazine, ultra detailed"
        ]

        styled_prompt_templates = {
            "photorealistic": prompt_templates,
            "illustration": [f"hand-drawn illustration of {prompt}, colorful and playful"],
            "minimalist": [f"flat vector-style minimalist icon of {prompt}"],
            "vintage": [f"vintage-style photo of {prompt}, film grain, retro colors"],
            "fantasy": [f"fantasy-style depiction of {prompt}, glowing and magical"]
        }

        final_options = styled_prompt_templates.get(style, []) + prompt_templates
        final_prompt = random.choice(final_options)

        # 🧠 Call Bedrock
        body = json.dumps({
            "text_prompts": [{"text": final_prompt}],
            "cfg_scale": 10,
            "steps": 50,
            "seed": 0
        })

        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body
        )

        response_body = json.loads(response["body"].read())
        base64_image = response_body['artifacts'][0]['base64']
        image_data = base64.b64decode(base64_image)

        # 🗂️ Save to S3 (🔧 uses FOLDER and BUCKET_NAME from above)
        filename = f"{FOLDER}/{uuid.uuid4().hex}.png"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=image_data,
            ContentType='image/png',
        )

        # 🌐 Construct public S3 URL (🔧 uses BUCKET_NAME + filename)
        image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"

        return {
            "statusCode": 200,
            "body": json.dumps({
                "prompt_used": final_prompt,
                "image_url": image_url
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            }
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            }
        }
