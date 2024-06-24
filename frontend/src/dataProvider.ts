import { fetchUtils } from "react-admin";

const apiUrl = "http://localhost:8000/api";
const httpClient = fetchUtils.fetchJson;

export const createDataProvider = () => {
  return {
    getList: async (resource: string, params: any) => {
      if (resource === "products") {
        try {
          const url = `${apiUrl}/products`;
          const headers = new Headers({
            Accept: "application/json",
            "Content-Type": "application/json",
          });
          const response = await httpClient(url, {
            method: "GET",
            headers: headers,
          });
          return response.json;
        } catch (error) {
          console.error(error);
          throw new Error("Failed to fetch products");
        }
      } else {
        throw new Error(`Unsupported resource: ${resource}`);
      }
    },
    create: async (resource, params) => {
      if (resource === "products") {
        try {
          const headers = new Headers({
            Accept: "application/json",
            "Content-Type": "application/json",
          });

          let endpoint;
          let body;

          // Determine the extraction method based on params
          if (params.data.url) {
            endpoint = `${apiUrl}/products/extract/url`;
            body = JSON.stringify({ url: params.data.url });
          } else if (params.data.text) {
            endpoint = `${apiUrl}/products/extract/text`;
            body = JSON.stringify({ large_text: params.data.text });
          } else if (params.data.pdf) {
            // Handle PDF file upload
            const formData = new FormData();
            formData.append("pdf_file", params.data.pdf.rawFile);

            endpoint = `${apiUrl}/products/extract/pdf`;
            body = formData;
            headers.delete("Content-Type"); // Let browser set the correct content type
          } else {
            throw new Error("Unsupported extraction method");
          }

          const response = await httpClient(endpoint, {
            method: "POST",
            body: body,
            headers: headers,
          });

          return { data: response.json };
        } catch (error) {
          console.error(error);
          throw new Error("Failed to extract product details");
        }
      } else {
        throw new Error(`Unsupported resource: ${resource}`);
      }
    },
  };
};
