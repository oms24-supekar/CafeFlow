
import { useEffect, useState } from "react";

type MenuItem = {
  id: number;
  name: string;
  price: number;
};

export default function App() {
  const [menu, setMenu] = useState<MenuItem[]>([]);
  const [cart, setCart] = useState<MenuItem[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/menu")
      .then((res) => {
        if (!res.ok) throw new Error("API unavailable");
        return res.json();
      })
      .then(setMenu)
      .catch(console.error);
  }, []);

  const total = cart.reduce(
    (sum, item) => sum + item.price, 0
  );

  return (
    <main style={{ padding: 32, fontFamily: "Arial" }}>
      <h1>CafeFlow ☕</h1>
      <p>Self-service café ordering demo</p>

      <h2>Menu</h2>
      {menu.map((item) => (
        <div key={item.id} style={{ margin: 12 }}>
          {item.name} — ₹{item.price}
          <button onClick={() => setCart([...cart, item])}>
            Add
          </button>
        </div>
      ))}

      <h2>Your cart</h2>
      <p>{cart.length} items</p>
      <h3>Total: ₹{total}</h3>
      <button onClick={() => setCart([])}>Clear cart</button>
    </main>
  );
}
