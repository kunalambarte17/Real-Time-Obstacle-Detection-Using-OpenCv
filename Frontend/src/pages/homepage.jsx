import { useNavigate } from "react-router-dom";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
      <h1 className="text-3xl font-bold mb-6">Welcome to Standalone Guidance System</h1>
      <button
        onClick={() => navigate("/cam")}
        className="px-6 py-3 bg-white text-indigo-600 font-semibold rounded-2xl shadow-lg hover:bg-gray-200"
      >
        Click to Start
      </button>
    </div>
  );
}
