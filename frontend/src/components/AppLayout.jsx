import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import ChatWidget from "./ChatWidget";

export default function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-slate-950">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
      <ChatWidget />
    </div>
  );
}
