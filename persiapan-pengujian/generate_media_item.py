import uuid
import random
import json
import os
from datetime import datetime, timedelta
import string
from typing import List, Dict, Any


MEDIA_TYPE = {
    "ARTIKEL": 1,
    "VIDEO": 2,
    "GALERI": 3
}

CONTENT_DISTRIBUTION = {
    MEDIA_TYPE["ARTIKEL"]: 0.6,
    MEDIA_TYPE["GALERI"]: 0.3,
    MEDIA_TYPE["VIDEO"]: 0.1
}

STATUS_DISETUJUI = 4

def load_json_data():
    with open('units.json', 'r') as f:
        units = json.load(f)
        
    with open('categories.json', 'r') as f:
        categories = json.load(f)

    return units, categories

def generate_predefined_tags():
    single_word_tags = [
        "penelitian", "akademik", "pendidikan", "ilmiah", "studi", "kajian",
        "acara", "seminar", "workshop", "konferensi", "pertemuan", "kegiatan",
        "sejarah", "dokumentasi", "arsip", "warisan", "heritage", "tradisi",
        "kampus", "universitas", "fakultas", "mahasiswa", "dosen", "alumni",
        "teknologi", "sains", "inovasi", "prestasi", "pencapaian", "karya",
        "pengabdian", "masyarakat", "internasional", "nasional", "komunitas", 
        "organisasi", "kolaborasi", "riset", "budaya", "ilmu", "jurnal",
        "publikasi", "gedung", "laboratorium", "perpustakaan", "fasilitas",
        "rektorat", "dekanat", "yudisium", "wisuda", "orientasi", "penerimaan"
    ]

    two_word_tags = [
        "penelitian ilmiah", "kajian akademik", "studi komprehensif",
        "sejarah universitas", "warisan budaya", "inovasi teknologi",
        "prestasi akademik", "publikasi ilmiah", "laboratorium riset",
        "dokumentasi kampus", "arsip sejarah", "perpustakaan pusat",
        "pengabdian masyarakat", "kolaborasi internasional", "kerja sama",
        "fakultas kedokteran", "fakultas hukum", "fakultas teknik",
        "fakultas ekonomi", "gedung rektorat", "upacara wisuda",
        "mahasiswa berprestasi", "dosen teladan", "alumni sukses",
        "kegiatan kemahasiswaan", "organisasi kampus", "komunitas akademik",
        "seminar nasional", "konferensi internasional", "workshop pelatihan",
        "perpustakaan digital", "sumber informasi", "karya ilmiah",
        "jurnal penelitian", "publikasi akademik", "basis data",
        "inovasi pendidikan", "metode pembelajaran", "fasilitas kampus",
        "program sarjana", "program pascasarjana", "program doktoral",
        "beasiswa pendidikan", "pertukaran mahasiswa", "sistem informasi"
    ]

    all_tags = single_word_tags + two_word_tags

    while len(all_tags) < 100:
        word1 = random.choice(single_word_tags)
        word2 = random.choice(single_word_tags)
        if word1 != word2:
            new_tag = f"{word1} {word2}"
            if new_tag not in all_tags and f"{word2} {word1}" not in all_tags:
                all_tags.append(new_tag)

    all_tags = all_tags[:100]

    tags = []
    for tag_name in all_tags:
        tag_id = uuid.uuid4()
        tags.append({"id": tag_id, "name": tag_name})

    return tags

def generate_random_date():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*10)

    random_days = random.randint(0, (end_date - start_date).days)
    random_date = start_date + timedelta(days=random_days)

    return random_date

def generate_title(media_type):
    prefixes = [
        "Dokumentasi", "Sejarah", "Perkembangan", "Kegiatan", "Peristiwa",
        "Acara", "Pertemuan", "Seminar", "Workshop", "Riset", "Penelitian",
        "Inovasi", "Prestasi", "Pencapaian", "Karya", "Kolaborasi"
    ]
    
    subjects = [
        "Mahasiswa", "Fakultas", "Universitas", "Dosen", "Akademik",
        "Kampus", "Pendidikan", "Pembelajaran", "Kebudayaan", "Ilmiah",
        "Teknologi", "Sains", "Pengabdian Masyarakat", "Alumni", "Kerjasama",
        "Internasional", "Nasional", "Komunitas", "Organisasi"
    ]
    
    type_names = {
        MEDIA_TYPE["ARTIKEL"]: "Artikel",
        MEDIA_TYPE["VIDEO"]: "Video",
        MEDIA_TYPE["GALERI"]: "Galeri"
    }
    
    return f"{random.choice(prefixes)} {random.choice(subjects)} {type_names[media_type]} UI Heritage"

def generate_description(num_paragraphs):
    paragraphs = []
    topics = [
        "sejarah perkembangan universitas",
        "peran kampus dalam pembangunan nasional",
        "tokoh-tokoh berpengaruh dalam komunitas akademik",
        "prestasi mahasiswa dan alumni",
        "inovasi penelitian dan pengabdian masyarakat",
        "kebijakan dan peraturan pendidikan tinggi",
        "pengembangan infrastruktur kampus",
        "kerjasama internasional dalam dunia akademik",
        "kontribusi kampus terhadap industri dan masyarakat",
        "kegiatan kemahasiswaan dan organisasi kampus"
    ]
    
    for _ in range(num_paragraphs):
        topic = random.choice(topics)
        sentences = random.randint(4, 8)
        paragraph = f"Dokumentasi {topic} merupakan bagian penting dari arsip UI Heritage. "
        paragraph += f"Dalam konteks ini, terdapat berbagai aspek yang perlu diperhatikan terkait {topic}. "
        paragraph += f"Selain itu, perkembangan {topic} juga memberikan gambaran tentang perjalanan institusi. "
        paragraph += f"Universitas Indonesia terus berkomitmen untuk mendokumentasikan {topic} sebagai bagian dari sejarah. "
        
        if sentences > 4:
            paragraph += f"Dengan demikian, pemahaman tentang {topic} dapat diwariskan kepada generasi berikutnya. "
        if sentences > 5:
            paragraph += f"Kajian mendalam mengenai {topic} juga menjadi perhatian dari berbagai pihak. "
        if sentences > 6:
            paragraph += f"Sumber daya yang tersedia dimanfaatkan untuk mengembangkan sistem dokumentasi {topic}. "
        if sentences > 7:
            paragraph += f"Nilai historis dari {topic} menjadikannya bagian tidak terpisahkan dari identitas kampus."
        
        paragraphs.append(paragraph)
    
    return "\n\n".join(paragraphs)

def generate_files(media_type):
    files = []
    
    if media_type == MEDIA_TYPE["ARTIKEL"]:
        num_images = random.randint(1, 2)
        for i in range(num_images):
            file_id = uuid.uuid4()
            files.append({
                "id": file_id,
                "file_name": f"artikel_image_{i+1}.jpg",
                "file_path": f"images/artikel_image_{i+1}_{file_id}.jpg",
                "file_type": "image/jpeg",
                "file_size": random.randint(100000, 400000),
                "order": i,
                "caption": f"Gambar dokumentasi {i+1}",
                "copyright": f"© Universitas Indonesia {random.randint(2015, 2025)}"
            })
    
    elif media_type == MEDIA_TYPE["GALERI"]:
        num_images = random.randint(3, 5)
        for i in range(num_images):
            file_id = uuid.uuid4()
            files.append({
                "id": file_id,
                "file_name": f"galeri_image_{i+1}.jpg",
                "file_path": f"images/galeri_image_{i+1}_{file_id}.jpg",
                "file_type": "image/jpeg",
                "file_size": random.randint(100000, 500000),
                "order": i,
                "caption": f"Galeri foto {i+1}",
                "copyright": f"© Universitas Indonesia {random.randint(2015, 2025)}"
            })
            
        if random.random() < 0.5:
            file_id = uuid.uuid4()
            thumbnail_path = f"video/thumbnails/video_thumbnail_{file_id}.jpg"
            files.append({
                "id": file_id,
                "file_name": "galeri_video.mp4",
                "file_path": f"videos/galeri_video_{file_id}.mp4",
                "file_type": "video/mp4",
                "file_size": random.randint(1000000, 10000000),
                "thumbnail_path": thumbnail_path,
                "order": num_images,
                "caption": "Video dokumentasi",
                "copyright": f"© Universitas Indonesia {random.randint(2015, 2025)}"
            })
    
    elif media_type == MEDIA_TYPE["VIDEO"]:
        file_id = uuid.uuid4()
        thumbnail_path = f"video/thumbnails/video_thumbnail_{file_id}.jpg"
        files.append({
            "id": file_id,
            "file_name": "video_konten.mp4",
            "file_path": f"videos/video_konten_{file_id}.mp4",
            "file_type": "video/mp4",
            "file_size": random.randint(1000000, 10000000),
            "thumbnail_path": thumbnail_path,
            "order": 0,
            "caption": "Video dokumentasi",
            "copyright": f"© Universitas Indonesia {random.randint(2015, 2025)}"
        })
    
    return files

def generate_reference_code(units_data, unit_ids, count):
    country_code = "ID"
    university_code = "UI"
    unit_codes = ""
    
    unit_dict = {unit["id"]: unit for unit in units_data}
    selected_units = [unit_dict[unit_id] for unit_id in unit_ids if unit_id in unit_dict]
    
    selected_units.sort(key=lambda x: x["order"])
    
    for unit in selected_units:
        unit_codes += unit["reference_code"]
    
    base_code = f"{country_code}-{university_code}-{unit_codes}"
    
    if count >= 1000000:
        unique_id = f"{count}"
    elif count >= 100000:
        unique_id = f"{count:06d}"
    elif count >= 10000:
        unique_id = f"{count:05d}"
    else:
        unique_id = f"{count:04d}"
    
    return f"{base_code}-{unique_id}"

def generate_media_item_sql(item_index, units_data, categories_data, all_tags, base_datetime):
    # Calculate statusUpdatedAt by adding item_index+1 seconds to the base time
    status_updated_at = base_datetime + timedelta(seconds=item_index+1)
    
    rand_val = random.random()
    cumulative = 0
    selected_type = None

    for media_type, probability in CONTENT_DISTRIBUTION.items():
        cumulative += probability
        if rand_val <= cumulative:
            selected_type = media_type
            break

    if selected_type is None:
        selected_type = MEDIA_TYPE["ARTIKEL"]

    media_item_id = uuid.uuid4()
    title = generate_title(selected_type)
    event_date = generate_random_date()

    if selected_type == MEDIA_TYPE["ARTIKEL"]:
        paragraphs = random.randint(2, 5)
        description = generate_description(paragraphs)
    else:
        description = ""

    active_categories = [c for c in categories_data if c.get("is_active", True) and c.get("deleted_at") is None]
    if not active_categories:
        raise ValueError("No active categories found")
    category = random.choice(active_categories)

    active_units = [u for u in units_data if u.get("is_active", True) and u.get("deleted_at") is None]
    if not active_units:
        raise ValueError("No active units found")
    num_units = random.randint(1, min(5, len(active_units)))
    selected_units = random.sample(active_units, num_units)
    unit_ids = [unit["id"] for unit in selected_units]

    num_tags = random.randint(0, 5)
    selected_tags = random.sample(all_tags, num_tags) if num_tags > 0 else []

    files = generate_files(selected_type)

    reference_code = generate_reference_code(units_data, unit_ids, item_index + 1)

    image_count = sum(1 for file in files if file["file_type"].startswith("image/"))
    video_count = sum(1 for file in files if file["file_type"].startswith("video/"))

    if selected_type == MEDIA_TYPE["ARTIKEL"]:
        if image_count == 0:
            media_extent = "1 tulisan"
        else:
            media_extent = f"1 tulisan dan {image_count} gambar"
    elif selected_type == MEDIA_TYPE["VIDEO"]:
        media_extent = "1 video"
    elif selected_type == MEDIA_TYPE["GALERI"]:
        media_extent = f"{image_count} gambar dan {video_count} video"
    else:
        media_extent = f"{len(files)} media"

    # Generate SQL statements
    sql = f"""
-- Insert media item
INSERT INTO media_items (
    id, title, description, type, contributor_id, status, category_id, 
    event_date, reference_code, description_level, media_extent, 
    archival_history, source, language, note, created_at, updated_at, status_updated_at
) VALUES (
    '{media_item_id}',
    '{title.replace("'", "''")}',
    '{description.replace("'", "''")}',
    {selected_type},
    '4eed0dc6-11e1-4d8b-a9fa-1163e4863441',
    {STATUS_DISETUJUI},
    '{category["id"]}',
    '{event_date.strftime("%Y-%m-%d")}',
    '{reference_code}',
    'Item',
    '{media_extent}',
    'Arsip dikumpulkan dari dokumentasi kegiatan universitas',
    'Dokumentasi internal Universitas Indonesia',
    'Indonesia',
    'Dokumen ini merupakan bagian dari koleksi UI Heritage',
    NOW(),
    NOW(),
    '{status_updated_at.strftime("%Y-%m-%d %H:%M:%S")}'
);
"""

    # Insert files
    for file in files:
        sql += f"""
-- Create file record
INSERT INTO files (id, file_name, file_path, file_type, file_size, thumbnail_path, created_at, updated_at)
VALUES (
    '{file['id']}', 
    '{file['file_name']}', 
    '{file['file_path']}', 
    '{file['file_type']}', 
    {file['file_size']}, 
    {("'" + file['thumbnail_path'] + "'") if 'thumbnail_path' in file else 'NULL'}, 
    NOW(), 
    NOW()
);
"""
    
    # Insert file associations
    sql += f"""
-- Insert media item files associations
INSERT INTO media_item_files (media_item_id, file_id, caption, "order", copyright, created_at, updated_at)
VALUES
"""
    for i, file in enumerate(files):
        sql += f"""('{media_item_id}', '{file["id"]}', '{file["caption"].replace("'", "''")}', {file["order"]}, '{file["copyright"].replace("'", "''")}', NOW(), NOW())"""
        if i < len(files) - 1:
            sql += ","
        sql += "\n"
    sql += ";\n"
    
    # Insert unit associations
    sql += f"""
-- Insert media item unit associations
INSERT INTO media_item_unit_approvals (media_item_id, unit_id, status, created_at, updated_at)
VALUES
"""
    for i, unit_id in enumerate(unit_ids):
        sql += f"""('{media_item_id}', '{unit_id}', {STATUS_DISETUJUI}, NOW(), NOW())"""
        if i < len(unit_ids) - 1:
            sql += ","
        sql += "\n"
    sql += ";\n"
    
    # Insert arsip approval
    sql += f"""
-- Insert media item arsip approval
INSERT INTO media_item_arsip_approvals (media_item_id, status, created_at, updated_at)
VALUES ('{media_item_id}', {STATUS_DISETUJUI}, NOW(), NOW());
"""
    
    # Insert tag associations
    if selected_tags:
        sql += f"""
-- Insert media item tag associations
INSERT INTO media_item_tags (media_item_id, tag_id, created_at, updated_at)
VALUES
"""
        for i, tag in enumerate(selected_tags):
            sql += f"""('{media_item_id}', '{tag["id"]}', NOW(), NOW())"""
            if i < len(selected_tags) - 1:
                sql += ","
            sql += "\n"
        sql += ";\n"
    
    return sql

def main():
    try:
        units_data, categories_data = load_json_data()

        predefined_tags = generate_predefined_tags()

        output_file = "generate_media_items.sql"
        
        # Base datetime to use for statusUpdatedAt incrementing
        base_datetime = datetime.now()

        with open(output_file, "w") as f:
            f.write("-- SQL Script to generate 200 media items for UI Heritage\n")
            f.write("-- Generated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            
            f.write("-- Creating 100 predefined tags\n")
            for tag in predefined_tags:
                f.write(f"""INSERT INTO tags (id, name, created_at, updated_at) 
VALUES ('{tag["id"]}', '{tag["name"].replace("'", "''")}', NOW(), NOW());\n""")
            
            f.write("\n-- Now creating 200 media items\n\n")

            for i in range(200):
                f.write(f"-- Media Item {i+1}\n")
                sql = generate_media_item_sql(i, units_data, categories_data, predefined_tags, base_datetime)
                f.write(sql)
                f.write("\n")
            
        print(f"Successfully generated SQL script: {output_file}")
        print(f"The script creates 100 predefined tags and 200 media items with the following distribution:")
        print(f"- Articles: {int(CONTENT_DISTRIBUTION[MEDIA_TYPE['ARTIKEL']] * 200)} items")
        print(f"- Galleries: {int(CONTENT_DISTRIBUTION[MEDIA_TYPE['GALERI']] * 200)} items")
        print(f"- Videos: {int(CONTENT_DISTRIBUTION[MEDIA_TYPE['VIDEO']] * 200)} items")
        print(f"Each item has statusUpdatedAt set with +1 second increments from the base time: {base_datetime}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()