import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { OverviewPage } from "./pages/OverviewPage";
import { PropertyPage } from "./pages/PropertyPage";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<OverviewPage />} />
        <Route path="properties/:slug" element={<PropertyPage />} />
      </Route>
    </Routes>
  );
}

export default App;
