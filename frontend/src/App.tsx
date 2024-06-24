import * as React from "react";
import {
  Admin,
  Resource,
  ListGuesser,
  EditGuesser,
  ShowGuesser,
  Create,
  SimpleForm,
  TextInput,
  FileInput,
  FileField,
} from "react-admin";
import { Layout } from "./Layout";
import { createDataProvider } from "./dataProvider";

interface Product {
  id?: string; // ID is optional for new products
  name: string;
  description: string;
  hs_code?: string;
  image_url?: string;
  location: Location;
  weight_kg: number;
  recycled_pct?: number;
  waste_pct?: number;
  lifetime_amount?: number;
  materials: Product[];
}

interface Location {
  id?: string; // ID is optional for new locations
  name: string;
  description?: string;
  country_code?: string;
  address?: string;
}

const ProductCreateForm: React.FC = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="url" label="URL" />
      <TextInput source="text" label="Text" />
      <FileInput source="pdf" label="PDF File" accept="application/pdf">
        <FileField source="rawFile" title="title" />
      </FileInput>
    </SimpleForm>
  </Create>
);

export const App: React.FC = () => (
  <Admin layout={Layout} dataProvider={createDataProvider()}>
    <Resource
      name="products"
      list={ListGuesser}
      edit={EditGuesser}
      show={ShowGuesser}
      create={ProductCreateForm}
    />
  </Admin>
);
