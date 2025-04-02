import { RouterProvider } from "react-router-dom";
import { router } from "@/core/router";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <>
      <Toaster />
      <RouterProvider router={router} />
    </>
  );
}

export default App;
