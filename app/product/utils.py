from fastapi import UploadFile, HTTPException, status
from slugify import slugify
from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}

# check if the directory exist or not
UPLOAD_DIR.mkdir(exist_ok=True)

async def save_upload_file(upload_file: UploadFile, sub_dir: str)->str: 

    ALLOWED_EXTENSION = [".jpg", ".jpeg", ".png", ".pdf"]

    if not upload_file or not upload_file.filename:
        return None

    # create file extension
    ext = Path(upload_file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type.")
    
    # Fake extensionvirus.exe.png 😬
    if upload_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type.")
    # create a filename
    filename = f"{uuid4().hex}{ext}"
    # create directory path 
    dir_path = UPLOAD_DIR / sub_dir
    # check if the directory exist or not
    dir_path.mkdir(parents=True, exist_ok=True) 
    # create file path
    file_path = dir_path / filename

    """
    User file upload karta hai
    FastAPI usay UploadFile object bana deta hai
    Tum read() se uska binary data nikalte ho
    Disk par nayi file banate ho
    Us data ko us file mein write kar dete ho

    Bonus tip (large files ke liye)

    Agar file bohat bari ho, read() poori file memory mein la deta hai (danger 😬).
    Better approach hoti hai:
    
    with file_path.open("wb") as f:
    while chunk := await upload_file.read(1024):  <------------------  tip
        f.write(chunk)

    """

   

    # “bhai jo file user ne bheji hai uska poora data memory mein la do”
    try: 
        content = await upload_file.read()
        with file_path.open("wb") as f: 
            f.write(content)
    except OSError as e:
        print(f"File system error: {e}")
    except Exception as e: 
        print(f"Something went wrong: {e}")

    return str(file_path)


def generate_slug(text: str) -> str:
    if not text:
        return ""
    return slugify(text)