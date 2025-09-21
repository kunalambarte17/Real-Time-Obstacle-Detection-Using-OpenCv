import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import HomePage from "./pages/homepage";
import CamPage from "./pages/cmapage";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cam" element={<CamPage />} />
      </Routes>
    </Router>
  );
}
