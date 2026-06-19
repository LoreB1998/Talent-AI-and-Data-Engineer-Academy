import os
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

FILE_PATH = "Esercitazioni Python/Foundry/9_DocumentRecognition/receipt.jpg"

def main():
    load_dotenv()
    endpoint = os.getenv("AZ_ENDPOINT")
    key = os.getenv("AZ_KEY")

    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))  # type: ignore

    with open(FILE_PATH, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-receipt",
            body=f,
            content_type="application/octet-stream"
        )

    result = poller.result()

    print("---- Receipt ----")
    if result.documents:
        for idx, receipt in enumerate(result.documents):
            print(f"Document {idx + 1}:")
            for name, field in receipt.fields.items(): # type: ignore
                if field is None:
                    print(f"{name}: None")
                    continue
                value = field.content
                confidence = field.confidence
                print(f"{name}: {value} (confidence: {confidence})")
    else:
        print("Nessun documento strutturato rilevato.")

if __name__ == "__main__":
    main()