// Dependency-free hash router so reloads/links keep the active page.
import { useEffect, useState } from "react";

export type Route = "live" | "incidents" | "account";
const ROUTES: Route[] = ["live", "incidents", "account"];

function current(): Route {
  const h = window.location.hash.replace(/^#\/?/, "") as Route;
  return ROUTES.includes(h) ? h : "live";
}

export function useHashRoute(): [Route, (r: Route) => void] {
  const [route, setRoute] = useState<Route>(current());
  useEffect(() => {
    const onHash = () => setRoute(current());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const navigate = (r: Route) => { window.location.hash = `/${r}`; };
  return [route, navigate];
}
