import boto3

def lambda_handler(event, context):
    text = event.get('text')
    source_lang = event.get('source', 'auto')
    target_lang = event.get('target', 'en')

    translate = boto3.client('translate')

    response = translate.translate_text(
        Text=text,
        SourceLanguageCode=source_lang,
        TargetLanguageCode=target_lang
    )

    return {
        'statusCode': 200,
        'translatedText': response['TranslatedText']
    }
