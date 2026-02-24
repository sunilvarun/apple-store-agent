import { useState, useEffect } from "react";
import axios from "axios";

export function useCatalog() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    axios.get("/api/catalog")
      .then(r => setProducts(r.data.products))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { products, loading, error };
}
