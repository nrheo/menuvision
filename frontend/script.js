async function uploadPDF() {
    const fileInput = document.getElementById('pdfUpload');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a PDF file first.');
        return;
    }

    try {
        // Step 1: Request pre-signed URL from backend
        const presignResponse = await fetch('http://localhost:3000/get-upload-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileName: file.name })
        });

        if (!presignResponse.ok) throw new Error('Failed to get pre-signed URL');
        const { uploadUrl, objectKey } = await presignResponse.json();

        // Step 2: Upload file to S3 using the pre-signed URL
        const s3Response = await fetch(uploadUrl, {
            method: "PUT",
            headers: {
                "Content-Type": "application/pdf"
            },
            body: file
        });

        if (!s3Response.ok) throw new Error('Upload to S3 failed');

        // Step 3: Start Step Function using objectKey
        const stepFunctionResponse = await fetch('http://localhost:3000/start-step-function', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ objectKey })
        });

        if (!stepFunctionResponse.ok) throw new Error('Failed to start Step Function');
        const result = await stepFunctionResponse.json();
        const executionArn = result.executionArn;

        // Step 4: Show waiting message and begin polling for result
        document.getElementById('translatedText').value = "Step function started. Please wait for results...";
        checkStepFunctionStatus(executionArn);

    } catch (err) {
        console.error(err);
        alert("Failed to process file: " + err.message);
    }
}

async function checkStepFunctionStatus(executionArn) {
    try {
        const response = await fetch(`http://localhost:3000/check-status?executionArn=${encodeURIComponent(executionArn)}`);
        const data = await response.json();

        if (data.status === 'SUCCEEDED') {
            const translatedText = data.result.translatedResult.translatedText;
            document.getElementById('translatedText').value = translatedText;
        } else if (data.status === 'RUNNING') {
            setTimeout(() => checkStepFunctionStatus(executionArn), 2000);
        } else {
            document.getElementById('translatedText').value = `Step Function failed: ${data.status}`;
        }
    } catch (err) {
        console.error("[ERROR polling step function]", err);
        document.getElementById('translatedText').value = "Failed to fetch translation result.";
    }
}

async function generateImage() {
    const item = document.getElementById('selectedItem').value;
    if (!item.trim()) {
        alert("Please enter a menu item.");
        return;
    }

    const container = document.getElementById('generatedImageContainer');
    container.innerHTML = "<p>🌀 Generating image...</p>";  // ✅ Loading spinner

    try {
        const response = await fetch('http://localhost:3000/generate-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item })
        });

        const raw = await response.json();
        const parsed = JSON.parse(raw.body);

        const imageUrl = parsed.image_url;
        const promptUsed = parsed.prompt_used;

        // ✅ Cache-busting with timestamp
        const bustedUrl = imageUrl + `?t=${Date.now()}`;

        const img = document.createElement('img');
        img.src = bustedUrl;
        img.alt = "Generated Menu Item";
        img.className = "generated-image";

        const caption = document.createElement('p');
        caption.className = "image-caption";
        caption.innerText = `Prompt used: "${promptUsed}"`;

        container.innerHTML = '';
        container.appendChild(img);
        container.appendChild(caption);

    } catch (err) {
        console.error(err);
        container.innerHTML = "<p style='color:red;'>❌ Image generation failed.</p>";
    }
}

