import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { setAuthToken } from "../api/client.js";

export default function OAuthComplete() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      setAuthToken(token);
      navigate("/repos", { replace: true });
    } else {
      navigate("/", { replace: true });
    }
  }, [params, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-sm text-mute">Signing you in…</p>
    </div>
  );
}
