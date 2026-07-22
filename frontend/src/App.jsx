import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import OAuthComplete from "./pages/OAuthComplete.jsx";
import RepoSelect from "./pages/RepoSelect.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import RepoDetail from "./pages/RepoDetail.jsx";
import { getAuthToken } from "./api/client.js";

function RequireAuth({ children }) {

  if (!getAuthToken()) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/oauth/complete" element={<OAuthComplete />} />
      <Route
        path="/repos"
        element={
          <RequireAuth>
            <RepoSelect />
          </RequireAuth>
        }
      />
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/repo/:repoName"
        element={
          <RequireAuth>
            <RepoDetail />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
