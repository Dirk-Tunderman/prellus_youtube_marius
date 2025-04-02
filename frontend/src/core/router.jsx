import { createBrowserRouter } from "react-router-dom";
import { RootLayout, NotFound } from "@/shared/components";
import { TranscriptPage } from "@/features/transcript/components";
import { ConfigPage } from "@/features/config/components";
import { DownloadsPage } from "@/features/downloads/components";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <NotFound />,
    children: [
      {
        index: true,
        element: <TranscriptPage />,
      },
      {
        path: "config",
        element: <ConfigPage />,
      },
      {
        path: "downloads",
        element: <DownloadsPage />,
      },
    ],
  },
]);
