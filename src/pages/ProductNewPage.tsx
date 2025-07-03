const handleSubmit = async (data) => {
  if (isSubmitting) return;

  // Validate and convert types
  const processedData = {
    ...data,
    name: data.name?.trim(),
    description: data.description?.trim(),
    category_id: Number(data.category_id || data.category),
    brand_id: Number(data.brand_id || data.brand),
    price: Number(data.price),
    condition: data.condition,
    attribute_value_ids: (data.attribute_value_ids || []).map(Number),
    images_upload: data.images_upload, // array of File objects
  };

  // Check for required fields
  const requiredFields = ['name', 'description', 'category_id', 'brand_id', 'price', 'condition', 'attribute_value_ids'];
  for (const field of requiredFields) {
    if (
      processedData[field] === undefined ||
      processedData[field] === null ||
      (Array.isArray(processedData[field]) && processedData[field].length === 0) ||
      (typeof processedData[field] === 'string' && !processedData[field].trim())
    ) {
      toast({
        title: 'Validation Error',
        description: `Field "${field}" is required.`,
        variant: 'destructive',
      });
      return;
    }
  }

  setIsSubmitting(true);
  try {
    const formData = new FormData();
    formData.append('name', processedData.name);
    formData.append('description', processedData.description);
    formData.append('category_id', String(processedData.category_id));
    formData.append('brand_id', String(processedData.brand_id));
    formData.append('price', String(processedData.price));
    formData.append('condition', processedData.condition);

    // Append attribute_value_ids as multiple fields
    processedData.attribute_value_ids.forEach((id) => {
      formData.append('attribute_value_ids', String(id));
    });

    // Append each image file individually
    if (processedData.images_upload && Array.isArray(processedData.images_upload)) {
      processedData.images_upload.forEach((file) => {
        formData.append('images_upload', file);
      });
    }

    // Log FormData for debugging
    for (let pair of formData.entries()) {
      console.log(pair[0] + ':', pair[1]);
    }

    // Send the request
    const result = await createProduct(formData);

    if (!result || !result.id) {
      throw new Error('Failed to create product: No product ID returned');
    }

    toast({
      title: 'Success',
      description: 'Product created successfully!',
    });
    // Redirect or update UI as needed
  } catch (error) {
    // Improved error logging
    if (error.response && error.response.data) {
      console.error('Backend error:', error.response.data);
      toast({
        title: 'Error',
        description: Object.entries(error.response.data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join('; '),
        variant: 'destructive',
      });
    } else {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create product',
        variant: 'destructive',
      });
    }
  } finally {
    setIsSubmitting(false);
  }
}; 