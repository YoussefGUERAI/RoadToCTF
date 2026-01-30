Similarly, certain file types may always contain a specific sequence of bytes in their header or footer. These can be used like a fingerprint or signature to determine whether the contents match the expected type. For example, JPEG files always begin with the bytes `FF D8 FF`.
This is a much more robust way of validating the file type.

## ExifTool :
ExifTool, it can be trivial to create a polyglot JPEG file containing malicious code within its metadata.

### 🔹 What is **Metadata**?

- **Definition:** Metadata is “data about data.” It describes or gives information about other data inside a file.
- In the context of images (like **JPEG, PNG, GIF**):
    - Metadata stores things like:
        - **Author / creator**
        - **Camera model**
        - **Date and time taken**
        - **GPS coordinates** (location where the photo was taken)
        - **Editing software used**
    - This data is not part of the visible image itself — it’s “extra info” embedded in the file.
### 🔹 What is **ExifTool**?

- **ExifTool** is a command-line utility used for reading, writing, and editing metadata in files (especially images, PDFs, audio, and video).
- Supports **many formats** (JPEG, PNG, PDF, MP3, etc.).
- Very popular among:
    - **Forensics investigators** (to check photo details).
    - **Photographers** (to edit image info).
    - **Hackers** (to inject malicious metadata payloads).![[Screenshot 2025-09-24 at 19.59.58.png]]

Even if the extension is **.php**, the polyglot is a **valid JPEG file** (it starts with the JPEG magic bytes), so it passed the image-type checks. 
**Server serves files** from that directory — depending on webserver config, files there might be served as static assets (no execution) or could be parsed by the PHP handler if they have a PHP extension and execution is enabled for that folder.