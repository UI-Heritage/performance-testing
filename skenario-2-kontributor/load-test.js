import http from "k6/http";
import { sleep, check, group } from "k6";
import { randomItem, randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";
import { SharedArray } from "k6/data";

export const options = {
  stages: [
    { duration: "1m", target: 10 },
    { duration: "1m30s", target: 10 },
    { duration: "1m", target: 25 },
    { duration: "1m30s", target: 25 },
    { duration: "1m30s", target: 50 },
    { duration: "2m", target: 50 },
    { duration: "30s", target: 15 },
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<20000"],
    http_req_failed: ["rate<0.05"],
  },
};

const metrics = {
  login_duration: new Trend("login_duration"),
  login_failed: new Rate("login_failed"),
  login_requests: new Counter("login_requests"),

  small_file_upload_duration: new Trend("small_file_upload_duration"),
  small_file_upload_failed: new Rate("small_file_upload_failed"),
  small_file_upload_requests: new Counter("small_file_upload_requests"),

  large_file_upload_init_duration: new Trend("large_file_upload_init_duration"),
  large_file_upload_init_failed: new Rate("large_file_upload_init_failed"),
  large_file_upload_init_requests: new Counter("large_file_upload_init_requests"),

  chunk_upload_duration: new Trend("chunk_upload_duration"),
  chunk_upload_failed: new Rate("chunk_upload_failed"),
  chunk_upload_requests: new Counter("chunk_upload_requests"),

  complete_upload_duration: new Trend("complete_upload_duration"),
  complete_upload_failed: new Rate("complete_upload_failed"),
  complete_upload_requests: new Counter("complete_upload_requests"),

  media_item_create_duration: new Trend("media_item_create_duration"),
  media_item_create_failed: new Rate("media_item_create_failed"),
  media_item_create_requests: new Counter("media_item_create_requests"),

  contributor_workflow_duration: new Trend("contributor_workflow_duration"),

  api_fetch_duration: new Trend("api_fetch_duration"),
  api_fetch_failed: new Rate("api_fetch_failed"),
};

const BASE_URL = "https://backend.ui-heritage.me/api/v1";

const CHUNK_SIZE = 1048576;

let categoriesCache = null;
let unitsCache = null;

function fetchCategories() {
  if (categoriesCache) {
    return categoriesCache;
  }

  const startTime = new Date();
  const categoriesResponse = http.get(`${BASE_URL}/web/categories?page=1&pageSize=10`, {
    headers: {
      Accept: "application/json",
    },
  });
  const endTime = new Date();

  metrics.api_fetch_duration.add(endTime - startTime);

  const success = check(categoriesResponse, {
    "categories fetch status is 200": (r) => r.status === 200,
    "categories fetch has data": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && Array.isArray(body.data);
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    metrics.api_fetch_failed.add(1);
    console.log(`Categories fetch failed: ${categoriesResponse.status}`);
    return [];
  }

  const responseBody = JSON.parse(categoriesResponse.body);

  const activeCategories = responseBody.data.filter((category) => category.isActive === true && category.deletedAt === null);

  categoriesCache = activeCategories;
  console.log(`Fetched ${activeCategories.length} active categories`);
  return activeCategories;
}

function fetchUnits() {
  if (unitsCache) {
    return unitsCache;
  }

  const startTime = new Date();
  const unitsResponse = http.get(`${BASE_URL}/web/units?page=1&pageSize=20`, {
    headers: {
      Accept: "application/json",
    },
  });
  const endTime = new Date();

  metrics.api_fetch_duration.add(endTime - startTime);

  const success = check(unitsResponse, {
    "units fetch status is 200": (r) => r.status === 200,
    "units fetch has data": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && Array.isArray(body.data);
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    metrics.api_fetch_failed.add(1);
    console.log(`Units fetch failed: ${unitsResponse.status}`);
    return [];
  }

  const responseBody = JSON.parse(unitsResponse.body);

  const activeUnits = responseBody.data.filter((unit) => unit.isActive === true && unit.deletedAt === null);

  unitsCache = activeUnits;
  console.log(`Fetched ${activeUnits.length} active units`);
  return activeUnits;
}

const contributors = new SharedArray("contributors", function () {
  return JSON.parse(open("../contributor_logins.json"));
});

const affPngContent = open("./test_data/AFF_PPT.png", "b");
const shot12MP4Content = open("./test_data/shot12.mp4", "b");
const chunk0Content = open("./test_data/chunks/chunk_0", "b");
const chunk1Content = open("./test_data/chunks/chunk_1", "b");
const chunk2Content = open("./test_data/chunks/chunk_2", "b");
const chunk3Content = open("./test_data/chunks/chunk_3", "b");

const MEDIA_TYPE = {
  ARTIKEL: 1,
  VIDEO: 2,
  GALERI: 3,
};

const CONTENT_DISTRIBUTION = {
  [MEDIA_TYPE.ARTIKEL]: 0.6,
  [MEDIA_TYPE.GALERI]: 0.3,
  [MEDIA_TYPE.VIDEO]: 0.1,
};

function selectMediaType() {
  const rand = Math.random();
  let cumulative = 0;

  for (const [type, probability] of Object.entries(CONTENT_DISTRIBUTION)) {
    cumulative += probability;
    if (rand <= cumulative) {
      return parseInt(type);
    }
  }

  return MEDIA_TYPE.ARTIKEL;
}

function generateTitle(mediaType) {
  const prefixes = ["Dokumentasi", "Sejarah", "Perkembangan", "Kegiatan", "Peristiwa", "Acara", "Pertemuan", "Seminar", "Workshop", "Riset", "Penelitian", "Inovasi", "Prestasi", "Pencapaian", "Karya", "Kolaborasi"];

  const subjects = ["Mahasiswa", "Fakultas", "Universitas", "Dosen", "Akademik", "Kampus", "Pendidikan", "Pembelajaran", "Kebudayaan", "Ilmiah"];

  const typeNames = {
    [MEDIA_TYPE.ARTIKEL]: "Artikel",
    [MEDIA_TYPE.VIDEO]: "Video",
    [MEDIA_TYPE.GALERI]: "Galeri",
  };

  return `${randomItem(prefixes)} ${randomItem(subjects)} ${typeNames[mediaType]} UI Heritage`;
}

function generateDescription(numParagraphs) {
  const paragraphs = [];
  const topics = ["sejarah perkembangan universitas", "peran kampus dalam pembangunan nasional", "tokoh-tokoh berpengaruh dalam komunitas akademik", "prestasi mahasiswa dan alumni", "inovasi penelitian dan pengabdian masyarakat"];

  for (let i = 0; i < numParagraphs; i++) {
    const topic = randomItem(topics);
    const sentences = randomIntBetween(4, 8);
    let paragraph = `Dokumentasi ${topic} merupakan bagian penting dari arsip UI Heritage. `;
    paragraph += `Dalam konteks ini, terdapat berbagai aspek yang perlu diperhatikan terkait ${topic}. `;
    paragraph += `Selain itu, perkembangan ${topic} juga memberikan gambaran tentang perjalanan institusi. `;
    paragraph += `Universitas Indonesia terus berkomitmen untuk mendokumentasikan ${topic} sebagai bagian dari sejarah. `;

    if (sentences > 4) {
      paragraph += `Dengan demikian, pemahaman tentang ${topic} dapat diwariskan kepada generasi berikutnya. `;
    }
    if (sentences > 5) {
      paragraph += `Kajian mendalam mengenai ${topic} juga menjadi perhatian dari berbagai pihak. `;
    }

    paragraphs.push(paragraph);
  }

  return paragraphs.join("\n\n");
}

function performLogin(user) {
  const payload = JSON.stringify(user);

  const params = {
    headers: {
      "X-DEV-API-KEY": "replace-with-your-api-key",
      "Content-Type": "application/json",
    },
  };

  metrics.login_requests.add(1);

  const startTime = new Date();
  const loginResponse = http.post(`${BASE_URL}/auth/sso-login`, payload, params);
  const endTime = new Date();

  metrics.login_duration.add(endTime - startTime);

  const success = check(loginResponse, {
    "login status is 200": (r) => r.status === 200,
    "login has access token": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.accessToken;
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    metrics.login_failed.add(1);
    console.log(`Login failed for user: ${user.user}`);
    return null;
  }

  const responseBody = JSON.parse(loginResponse.body);
  return {
    accessToken: responseBody.data.accessToken,
    userId: responseBody.data.user.id,
    username: responseBody.data.user.username,
  };
}

function uploadSmallFile(token) {
  metrics.small_file_upload_requests.add(1);

  const now = new Date();
  const year = now.getFullYear().toString();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  console.log(`Uploading image: AFF_PPT.png`);

  const startTime = new Date();

  const formData = {
    file: http.file(affPngContent, "AFF_PPT.png", "image/png"),
    eventYear: year,
    eventMonth: month,
    eventDay: day,
  };

  const uploadResponse = http.post(`${BASE_URL}/files/upload`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
    timeout: "120s",
  });

  const endTime = new Date();
  metrics.small_file_upload_duration.add(endTime - startTime);

  console.log(`Small file upload response: ${uploadResponse.status}`);

  const success = check(uploadResponse, {
    "small file upload status is 200": (r) => r.status === 200,
    "small file upload has file data": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.id;
      } catch (e) {
        console.log(`Error parsing response: ${e}`);
        return false;
      }
    },
  });

  if (!success) {
    metrics.small_file_upload_failed.add(1);
    console.log(`Small file upload failed: ${uploadResponse.status}`);
    console.log(`Response body: ${uploadResponse.body}`);
    return null;
  }

  const responseBody = JSON.parse(uploadResponse.body);
  return {
    fileId: responseBody.data.id,
    fileName: responseBody.data.fileName,
    filePath: responseBody.data.filePath,
    fileType: responseBody.data.fileType,
  };
}

function initiateLargeFileUpload(token) {
  metrics.large_file_upload_init_requests.add(1);

  const now = new Date();
  const year = now.getFullYear().toString();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  console.log(`Initiating large file upload with initialize=true for shot12.mp4`);

  const fileSize = shot12MP4Content.byteLength;
  
  const dummyContent = new Uint8Array(1).buffer;
  
  const formData = {
    file: http.file(dummyContent, "dummy.txt", "text/plain"),
    fileName: "shot 12.mp4",
    initialize: "true",
    fileSize: fileSize.toString(),
    fileType: "video/mp4",
    eventYear: year,
    eventMonth: month,
    eventDay: day,
  };

  const startTime = new Date();
  const uploadResponse = http.post(`${BASE_URL}/files/upload`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
    timeout: "60s",
  });
  const endTime = new Date();

  metrics.large_file_upload_init_duration.add(endTime - startTime);

  console.log(`Large file init response status: ${uploadResponse.status}`);
  console.log(`Response body: ${uploadResponse.body}`);

  const success = check(uploadResponse, {
    "large file init status is 200": (r) => r.status === 200,
    "large file init has uploadId": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.uploadId;
      } catch (e) {
        console.log(`Error parsing response: ${e}`);
        return false;
      }
    },
  });

  if (!success) {
    metrics.large_file_upload_init_failed.add(1);
    console.log(`Large file upload initiation failed: ${uploadResponse.status}`);
    return null;
  }

  const responseBody = JSON.parse(uploadResponse.body);
  return {
    uploadId: responseBody.data.uploadId,
    chunkSize: responseBody.data.chunkSize,
    totalSize: responseBody.data.totalSize,
  };
}

function uploadChunk(token, uploadId, chunkNumber) {
  metrics.chunk_upload_requests.add(1);

  let chunkContent;
  if (chunkNumber === 0) {
    chunkContent = chunk0Content;
  } else if (chunkNumber === 1) {
    chunkContent = chunk1Content;
  } else if (chunkNumber === 2) {
    chunkContent = chunk2Content;
  } else if (chunkNumber === 3) {
    chunkContent = chunk3Content;
  } else {
    console.log(`Error: Chunk number ${chunkNumber} is out of range (0-3)`);
    metrics.chunk_upload_failed.add(1);
    return false;
  }

  console.log(`Uploading chunk ${chunkNumber}`);

  const formData = {
    uploadId: uploadId,
    chunkNumber: chunkNumber,
    chunk: http.file(chunkContent, `chunk_${chunkNumber}`, "application/octet-stream"),
  };

  const startTime = new Date();
  const chunkResponse = http.post(`${BASE_URL}/files/upload/chunk`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });
  const endTime = new Date();

  metrics.chunk_upload_duration.add(endTime - startTime);

  console.log(`Chunk ${chunkNumber} upload response: ${chunkResponse.status}`);
  if (chunkResponse.status !== 200) {
    console.log(`Error body: ${chunkResponse.body}`);
  }

  const success = check(chunkResponse, {
    "chunk upload status is 200": (r) => r.status === 200,
  });

  if (!success) {
    metrics.chunk_upload_failed.add(1);
    console.log(`Chunk upload failed: ${chunkResponse.status}`);
    return false;
  }

  return true;
}

function completeUpload(token, uploadId) {
  metrics.complete_upload_requests.add(1);

  const formData = {
    uploadId: uploadId,
  };

  const startTime = new Date();
  const completeResponse = http.post(`${BASE_URL}/files/upload/complete`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });
  const endTime = new Date();

  metrics.complete_upload_duration.add(endTime - startTime);

  console.log(`Complete upload response: ${completeResponse.status}`);
  if (completeResponse.status !== 200) {
    console.log(`Error body: ${completeResponse.body}`);
  }

  const success = check(completeResponse, {
    "complete upload status is 200": (r) => r.status === 200,
    "complete upload has file data": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.id;
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    metrics.complete_upload_failed.add(1);
    console.log(`Complete upload failed: ${completeResponse.status}`);
    return null;
  }

  const responseBody = JSON.parse(completeResponse.body);
  return {
    fileId: responseBody.data.id,
    fileName: responseBody.data.fileName,
    filePath: responseBody.data.filePath,
    fileType: responseBody.data.fileType,
    thumbnailPath: responseBody.data.thumbnailPath || "",
  };
}

function createMediaItem(token, mediaType, files) {
  metrics.media_item_create_requests.add(1);

  const now = new Date();
  const eventYear = now.getFullYear().toString();
  const eventMonth = String(now.getMonth() + 1).padStart(2, "0");
  const eventDay = String(now.getDate()).padStart(2, "0");

  const categories = fetchCategories();
  const units = fetchUnits();

  const categoryId = categories.length > 0 ? randomItem(categories).id : null;
  if (!categoryId) {
    console.log("No categories available, cannot create media item");
    return null;
  }

  const numUnits = randomIntBetween(1, Math.min(3, units.length));
  const selectedUnits = [];
  const unitsCopy = [...units];

  for (let i = 0; i < numUnits; i++) {
    if (unitsCopy.length === 0) break;
    const randomIndex = Math.floor(Math.random() * unitsCopy.length);
    selectedUnits.push(unitsCopy[randomIndex].id);
    unitsCopy.splice(randomIndex, 1);
  }

  const tags = ["penelitian", "akademik", "pendidikan", "ilmiah", "studi", "kajian", "acara", "seminar", "workshop", "konferensi", "pertemuan", "kegiatan"];

  const numTags = randomIntBetween(1, 5);
  const selectedTags = [];

  for (let i = 0; i < numTags; i++) {
    if (i >= tags.length) break;
    const randomIndex = Math.floor(Math.random() * tags.length);
    selectedTags.push(tags[randomIndex]);
    tags.splice(randomIndex, 1);
  }

  const fileEntries = files.map((file, index) => ({
    fileId: file.fileId,
    caption: `File ${index + 1} - ${file.fileName}`,
    copyright: `© Universitas Indonesia ${now.getFullYear()}`,
    order: index + 1,
  }));

  const payload = {
    title: generateTitle(mediaType),
    type: mediaType,
    categoryId: categoryId,
    eventYear: eventYear,
    eventMonth: eventMonth,
    eventDay: eventDay,
    archivalHistory: "Dokumen ini merupakan arsip yang dikumpulkan dari kegiatan universitas",
    source: "Dokumentasi internal Universitas Indonesia",
    language: "Indonesia",
    note: "Dokumen ini merupakan bagian dari koleksi UI Heritage",
    files: fileEntries,
    tags: selectedTags,
    unitIds: selectedUnits,
  };

  if (mediaType === MEDIA_TYPE.ARTIKEL || mediaType === MEDIA_TYPE.GALERI) {
    const paragraphCount = randomIntBetween(2, 5);
    payload.description = generateDescription(paragraphCount);
  }

  console.log(`Creating media item with ${files.length} files, type: ${mediaType}`);

  const startTime = new Date();
  const createResponse = http.post(`${BASE_URL}/media-items`, JSON.stringify(payload), {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  const endTime = new Date();

  metrics.media_item_create_duration.add(endTime - startTime);

  console.log(`Media item creation response: ${createResponse.status}`);
  if (createResponse.status !== 200 && createResponse.status !== 201) {
    console.log(`Error body: ${createResponse.body}`);
  }

  const success = check(createResponse, {
    "media item creation status is 200 or 201": (r) => r.status === 200 || r.status === 201,
    "media item creation has data": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.data && body.data.id;
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    metrics.media_item_create_failed.add(1);
    console.log(`Media item creation failed: ${createResponse.status}`);
    return null;
  }

  return JSON.parse(createResponse.body).data;
}

export default function () {
  if (!categoriesCache) {
    console.log("Fetching and caching categories...");
    fetchCategories();
  }

  if (!unitsCache) {
    console.log("Fetching and caching units...");
    fetchUnits();
  }

  const startIterationTime = new Date();

  const contributor = randomItem(contributors);

  group("Step 1: SSO Login", function () {
    const loginInfo = performLogin(contributor);
    if (!loginInfo) {
      console.log("Login failed, aborting iteration");
      return;
    }

    const token = loginInfo.accessToken;

    sleep(randomIntBetween(1, 3));

    const mediaType = selectMediaType();
    console.log(`Creating media type: ${mediaType}`);

    group("Step 2: Upload Files", function () {
      const files = [];

      if (mediaType === MEDIA_TYPE.ARTIKEL) {
        const numImages = randomIntBetween(1, 2);

        for (let i = 0; i < numImages; i++) {
          console.log(`Uploading image ${i + 1} for article`);
          const fileInfo = uploadSmallFile(token);
          if (fileInfo) {
            files.push(fileInfo);
          }
          sleep(randomIntBetween(1, 2.5));
        }
      } else if (mediaType === MEDIA_TYPE.VIDEO) {
        console.log("Uploading video file");

        const initiateInfo = initiateLargeFileUpload(token);

        if (initiateInfo) {
          sleep(randomIntBetween(0.8, 1.5));

          const totalChunks = 4;

          console.log(`Will upload ${totalChunks} chunks for video`);

          let allChunksSuccess = true;
          for (let i = 0; i < totalChunks; i++) {
            console.log(`Uploading chunk ${i} of ${totalChunks}`);
            const chunkSuccess = uploadChunk(token, initiateInfo.uploadId, i);
            if (!chunkSuccess) {
              allChunksSuccess = false;
              break;
            }
            sleep(randomIntBetween(0.5, 1));
          }

          if (allChunksSuccess) {
            sleep(randomIntBetween(1, 2));

            console.log("Completing chunked upload");
            const fileInfo = completeUpload(token, initiateInfo.uploadId);
            if (fileInfo) {
              files.push(fileInfo);
            }
          }
        }
      } else if (mediaType === MEDIA_TYPE.GALERI) {
        const numImages = randomIntBetween(3, 5);

        for (let i = 0; i < numImages; i++) {
          console.log(`Uploading image ${i + 1} for gallery`);
          const fileInfo = uploadSmallFile(token);
          if (fileInfo) {
            files.push(fileInfo);
          }
          sleep(randomIntBetween(1, 2.5));
        }

        if (Math.random() < 0.5) {
          console.log("Adding video to gallery");

          sleep(randomIntBetween(2, 4));

          const initiateInfo = initiateLargeFileUpload(token);

          if (initiateInfo) {
            sleep(randomIntBetween(0.8, 1.5));

            const totalChunks = 4;

            let allChunksSuccess = true;
            for (let i = 0; i < totalChunks; i++) {
              console.log(`Uploading chunk ${i} of ${totalChunks} for gallery video`);
              const chunkSuccess = uploadChunk(token, initiateInfo.uploadId, i);
              if (!chunkSuccess) {
                allChunksSuccess = false;
                break;
              }
              sleep(randomIntBetween(0.5, 1));
            }

            if (allChunksSuccess) {
              sleep(randomIntBetween(1, 2));
              console.log("Completing gallery video upload");
              const fileInfo = completeUpload(token, initiateInfo.uploadId);
              if (fileInfo) {
                files.push(fileInfo);
              }
            }
          }
        }
      }

      sleep(randomIntBetween(2, 4));

      if (files.length > 0) {
        group("Step 3: Create Media Item", function () {
          const mediaItem = createMediaItem(token, mediaType, files);

          if (mediaItem) {
            console.log(`Successfully created media item: ${mediaItem.id}`);
          } else {
            console.log("Media item creation failed");
          }
        });
      } else {
        console.log("No files uploaded, cannot create media item");
      }
    });
  });

  const endIterationTime = new Date();
  const totalDuration = endIterationTime - startIterationTime;
  metrics.contributor_workflow_duration.add(totalDuration);

  sleep(randomIntBetween(3, 8));
}