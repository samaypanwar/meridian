import { BrowserRouter, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import SourceDetail from "./pages/SourceDetail";
import Capture from "./pages/Capture";
import Review from "./pages/Review";
import Goals from "./pages/Goals";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/sources/:id" element={<SourceDetail />} />
        <Route path="/sources/:id/capture" element={<Capture />} />
        <Route path="/review" element={<Review />} />
        <Route path="/goals" element={<Goals />} />
      </Routes>
    </BrowserRouter>
  );
}
