# Product Creation: Sending Campuses and Images (Frontend–Backend Integration Guide)

## Overview
This document explains how to correctly send **campuses** and **images** from the frontend to the backend during product creation, and highlights common mistakes to avoid. It is intended for frontend developers and AI agents working on the integration with a Django REST Framework backend.

---

## 1. Campuses (Many-to-Many Field)

### Backend Expectation
- The backend expects a field called `campus` (not `campus_id` or `campus_ids`).
- This field should be sent as a **list of IDs** (for JSON) or as **multiple `campus` fields** in `FormData` (for multipart/form-data).
- Example (FormData):
  ```
  campus=1
  campus=2
  campus=3
  ```

### Frontend Implementation
- When using `FormData`, append each selected campus as:
  ```js
  selectedCampusIds.forEach(id => formData.append('campus', String(id)));
  ```
- **Do NOT** use `campus_id` or `campus_ids` for many-to-many fields.

### Common Mistake
- Renaming the field to `campus_id` in the API context or helper functions. This will cause the backend to ignore the campuses.

---

## 2. Images (Multiple File Upload)

### Backend Expectation
- The backend expects multiple files under the key `images_upload` (not `images`).
- Example (FormData):
  ```
  images_upload: <File1>
  images_upload: <File2>
  images_upload: <File3>
  ```

### Frontend Implementation
- When using `FormData`, append each image file as:
  ```js
  images.forEach(image => formData.append('images_upload', image.file));
  ```
- If you want to indicate a primary image, you may send an additional field (e.g., `primary_image_index`), but only if the backend supports it.

### Common Mistake
- Renaming `images_upload` to `images` in the API context or helper functions. The backend will not recognize the files if the field name is changed.
- Adding extra fields like `is_primary` for each image unless the backend expects them.

---

## 3. General Advice
- **Do not modify or rename fields in the API context if you are already using the correct field names in the `FormData`.**
- Always check the backend serializer for the exact field names and types expected.
- Use browser dev tools to inspect the actual network request and confirm the correct fields are being sent.

---

## 4. Example: Correct FormData Construction
```js
const formData = new FormData();
formData.append('name', productData.name);
formData.append('description', productData.description);
formData.append('category_id', productData.category_id);
formData.append('brand_id', productData.brand_id);
formData.append('price', productData.price);
formData.append('condition', productData.condition);
productData.attribute_value_ids.forEach(id => formData.append('attribute_value_ids', String(id)));
selectedCampusIds.forEach(id => formData.append('campus', String(id)));
images.forEach(image => formData.append('images_upload', image.file));
// Optionally, if supported by backend:
// formData.append('primary_image_index', String(primaryIndex));
```

---

## 5. Troubleshooting
- If campuses or images are not being saved, check:
  - The field names in the request payload (should be `campus` and `images_upload`).
  - That you are not renaming or restructuring these fields in the API context or helper functions.
  - Backend error messages for clues about missing or misnamed fields.

---

## 6. Summary Table
| Field      | FormData Key      | Backend Expects      | Notes                       |
|------------|-------------------|----------------------|-----------------------------|
| Campuses   | campus (multiple) | campus (many=True)   | Do not use campus_id        |
| Images     | images_upload     | images_upload (list) | Do not use images           |

---

**Follow these guidelines to ensure campuses and images are sent and saved correctly during product creation.** 