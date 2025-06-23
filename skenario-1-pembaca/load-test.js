import http from "k6/http";
import { sleep, check, group } from "k6";
import { randomItem, randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";

export const options = {
  stages: [
    { duration: "1m", target: 200 },
    { duration: "1m30s", target: 200 },
    { duration: "1m", target: 500 },
    { duration: "1m30s", target: 500 },
    { duration: "1m30s", target: 1000 },
    { duration: "2m", target: 1000 },
    { duration: "30s", target: 300 },
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"],
    http_req_failed: ["rate<0.01"],
  },
};

const metrics = {
  categories_duration: new Trend("categories_duration"),
  categories_failed: new Rate("categories_failed"),
  categories_requests: new Counter("categories_requests"),

  units_duration: new Trend("units_duration"),
  units_failed: new Rate("units_failed"),
  units_requests: new Counter("units_requests"),

  media_items_search_duration: new Trend("media_items_search_duration"),
  media_items_search_failed: new Rate("media_items_search_failed"),
  media_items_search_requests: new Counter("media_items_search_requests"),

  media_item_detail_duration: new Trend("media_item_detail_duration"),
  media_item_detail_failed: new Rate("media_item_detail_failed"),
  media_item_detail_requests: new Counter("media_item_detail_requests"),

  view_increment_duration: new Trend("view_increment_duration"),
  view_increment_failed: new Rate("view_increment_failed"),
  view_increment_requests: new Counter("view_increment_requests"),
};

const BASE_URL = "https://backend.ui-heritage.me/api/v1";

let cachedUnits = [];
let cachedCategories = [];

function fetchUnits(headers) {
  if (cachedUnits.length === 0) {
    const response = http.get(`${BASE_URL}/web/units?page=1&pageSize=50`, { headers });
    if (response.status === 200) {
      try {
        const responseData = JSON.parse(response.body);
        if (responseData.data && Array.isArray(responseData.data)) {
          cachedUnits = responseData.data.filter((unit) => unit.isActive && !unit.deletedAt);
        }
      } catch (e) {
        console.log("Error parsing units response:", e);
      }
    }
  }
  return cachedUnits;
}

function fetchCategories(headers) {
  if (cachedCategories.length === 0) {
    const response = http.get(`${BASE_URL}/web/categories?page=1&pageSize=50`, { headers });
    if (response.status === 200) {
      try {
        const responseData = JSON.parse(response.body);
        if (responseData.data && Array.isArray(responseData.data)) {
          cachedCategories = responseData.data.filter((category) => category.isActive && !category.deletedAt);
        }
      } catch (e) {
        console.log("Error parsing categories response:", e);
      }
    }
  }
  return cachedCategories;
}

const searchTerms = ["Dokumentasi", "Sejarah", "Perkembangan", "Kegiatan", "Peristiwa", "Acara", "Pertemuan", "Seminar", "Workshop", "Riset", "Penelitian", "Inovasi", "Prestasi", "Pencapaian", "Karya", "Kolaborasi", "Mahasiswa", "Fakultas", "Universitas", "Dosen", "Akademik", "Kampus", "Pendidikan", "Pembelajaran", "Kebudayaan", "Ilmiah"];

function randomDate() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 5);

  const randomTime = start.getTime() + Math.random() * (end.getTime() - start.getTime());
  const date = new Date(randomTime);

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function buildSearchParams() {
  let params = [];

  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  if (Math.random() < 0.7) {
    params.push("page=1", "pageSize=20");
  } else {
    params.push("page=1", "pageSize=50");
  }

  if (Math.random() < 0.6) {
    params.push(`search=${randomItem(searchTerms)}`);
  }

  if (Math.random() < 0.6) {
    const sortOptions = ["-view_count", "-upvote_count", "-event_date"];

    const sortDistribution = Math.random();
    if (sortDistribution < 0.42) {
      params.push(`sort=${sortOptions[0]}`);
    } else if (sortDistribution < 0.75) {
      params.push(`sort=${sortOptions[1]}`);
    } else {
      params.push(`sort=${sortOptions[2]}`);
    }
  }

  if (Math.random() < 0.5) {
    const typeDistribution = Math.random();
    if (typeDistribution < 0.6) {
      params.push("types=1");
    } else if (typeDistribution < 0.9) {
      params.push("types=3");
    } else {
      params.push("types=2");
    }
  }

  const filterDistribution = Math.random();

  if (filterDistribution < 0.6) {
    if (Math.random() < 0.4 || filterDistribution < 0.4) {
      const filterType = Math.random();
      if (filterType < 0.33) {
        const availableUnits = fetchUnits(headers);
        if (availableUnits.length > 0) {
          params.push(`unit=${randomItem(availableUnits).id}`);
        }
      } else if (filterType < 0.66) {
        const availableCategories = fetchCategories(headers);
        if (availableCategories.length > 0) {
          params.push(`category=${randomItem(availableCategories).id}`);
        }
      } else {
        const startDate = randomDate();
        const endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + randomIntBetween(1, 30));
        const formattedEndDate = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, "0")}-${String(endDate.getDate()).padStart(2, "0")}`;

        params.push(`startDate=${startDate}`, `endDate=${formattedEndDate}`);
      }
    } else {
      const availableUnits = fetchUnits(headers);
      if (availableUnits.length > 0) {
        params.push(`unit=${randomItem(availableUnits).id}`);
      }

      const availableCategories = fetchCategories(headers);
      if (availableCategories.length > 0) {
        params.push(`category=${randomItem(availableCategories).id}`);

        if (Math.random() < 0.5) {
          const startDate = randomDate();
          const endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + randomIntBetween(1, 30));
          const formattedEndDate = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, "0")}-${String(endDate.getDate()).padStart(2, "0")}`;

          params.push(`startDate=${startDate}`, `endDate=${formattedEndDate}`);
        }
      }
    }
  }

  return params.length > 0 ? `?${params.join("&")}` : "";
}

export default function () {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  group("Step 1: Get Categories", function () {
    metrics.categories_requests.add(1);

    const startTime = new Date();
    let categoriesResponse = http.get(`${BASE_URL}/web/categories?page=1&pageSize=20`, { headers });
    const endTime = new Date();

    metrics.categories_duration.add(endTime - startTime);

    const success = check(categoriesResponse, {
      "categories status is 200": (r) => r.status === 200,
      "categories has data": (r) => JSON.parse(r.body).data !== undefined,
    });

    if (!success) {
      metrics.categories_failed.add(1);
    }

    if (cachedCategories.length === 0) {
      fetchCategories(headers);
    }
  });

  sleep(randomIntBetween(1, 3));

  group("Step 2: Get Units", function () {
    metrics.units_requests.add(1);

    const startTime = new Date();
    let unitsResponse = http.get(`${BASE_URL}/web/units?page=1&pageSize=20`, { headers });
    const endTime = new Date();

    metrics.units_duration.add(endTime - startTime);

    const success = check(unitsResponse, {
      "units status is 200": (r) => r.status === 200,
      "units has data": (r) => JSON.parse(r.body).data !== undefined,
    });

    if (!success) {
      metrics.units_failed.add(1);
    }

    if (cachedUnits.length === 0) {
      fetchUnits(headers);
    }
  });

  sleep(randomIntBetween(1, 3));

  let mediaItemId = null;
  group("Step 3: Search Media Items", function () {
    metrics.media_items_search_requests.add(1);

    const params = buildSearchParams();

    const startTime = new Date();
    let mediaItemsResponse = http.get(`${BASE_URL}/media-items${params}`, { headers });
    const endTime = new Date();

    metrics.media_items_search_duration.add(endTime - startTime);

    const success = check(mediaItemsResponse, {
      "media-items status is 200": (r) => r.status === 200,
      "media-items has data": (r) => JSON.parse(r.body).data !== undefined,
    });

    if (!success) {
      metrics.media_items_search_failed.add(1);
    }

    try {
      const mediaItems = JSON.parse(mediaItemsResponse.body).data;
      if (mediaItems && mediaItems.length > 0) {
        mediaItemId = randomItem(mediaItems).id;
      }
    } catch (e) {
      console.log("Error parsing media items response:", e);
    }
  });

  sleep(randomIntBetween(2, 5));

  if (mediaItemId) {
    group("Step 4: Get Media Item Detail", function () {
      metrics.media_item_detail_requests.add(1);

      const startTime = new Date();
      let mediaItemResponse = http.get(`${BASE_URL}/media-items/${mediaItemId}`, { headers });
      const endTime = new Date();

      metrics.media_item_detail_duration.add(endTime - startTime);

      const success = check(mediaItemResponse, {
        "media-item status is 200": (r) => r.status === 200,
        "media-item has data": (r) => JSON.parse(r.body).data !== undefined,
      });

      if (!success) {
        metrics.media_item_detail_failed.add(1);
      }
    });

    sleep(randomIntBetween(5, 15));

    group("Step 5: Increment View Count", function () {
      metrics.view_increment_requests.add(1);

      const startTime = new Date();
      let incrementViewResponse = http.post(`${BASE_URL}/media-items/${mediaItemId}/view`, null, { headers });
      const endTime = new Date();

      metrics.view_increment_duration.add(endTime - startTime);

      const success = check(incrementViewResponse, {
        "increment view status is 200": (r) => r.status === 200,
      });

      if (!success) {
        metrics.view_increment_failed.add(1);
      }
    });
  }

  sleep(randomIntBetween(3, 8));
}