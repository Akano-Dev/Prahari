import { useRef, useState } from "react";
import type { User } from "../types";
import { api } from "../api/client";
import { Avatar } from "../components/Avatar";

// Downscale a picked image to <=256px and return a compact JPEG data-URL,
// so the stored avatar stays small (well under the server's size cap).
function downscale(file: File, max = 256): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const reader = new FileReader();
    reader.onload = () => { img.src = reader.result as string; };
    reader.onerror = reject;
    img.onload = () => {
      const scale = Math.min(1, max / Math.max(img.width, img.height));
      const w = Math.round(img.width * scale), h = Math.round(img.height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = w; canvas.height = h;
      const ctx = canvas.getContext("2d")!;
      ctx.drawImage(img, 0, 0, w, h);
      resolve(canvas.toDataURL("image/jpeg", 0.85));
    };
    img.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function Account({ user, onUpdated, onSignOut }: {
  user: User; onUpdated: (u: User) => void; onSignOut: () => void;
}) {
  const [name, setName] = useState(user.display_name);
  const [avatar, setAvatar] = useState<string | null | undefined>(user.avatar);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const dirty = name !== user.display_name || avatar !== user.avatar;
  const preview: User = { ...user, display_name: name, avatar };

  const pick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try { setAvatar(await downscale(f)); setMsg(""); }
    catch { setMsg("Could not read that image."); }
  };

  const save = async () => {
    setBusy(true); setMsg("");
    try {
      const updated = await api.updateProfile({ display_name: name, avatar: avatar ?? "" });
      onUpdated(updated);
      setMsg("Saved ✓");
    } catch (e) { setMsg((e as Error).message); } finally { setBusy(false); }
  };

  const since = user.created_at ? new Date(user.created_at).toLocaleDateString(undefined,
    { year: "numeric", month: "long", day: "numeric" }) : "—";

  return (
    <div className="page account">
      <div className="panel hero" style={{ marginInline: 0 }}>
        <div className="eyebrow">Your profile</div>
        <h1>Account <span className="grad">settings</span></h1>
        <p>Personalize your operator profile. Your picture and name show across the dashboard.</p>
      </div>

      <div className="account-grid">
        <div className="panel">
          <h3>Profile picture</h3>
          <div className="avatar-edit">
            <Avatar user={preview} size={120} />
            <div className="avatar-actions">
              <input ref={fileRef} type="file" accept="image/*" hidden onChange={pick} />
              <button className="btn" onClick={() => fileRef.current?.click()}>Upload picture</button>
              {avatar && <button className="btn ghost" onClick={() => setAvatar(null)}>Remove</button>}
              <div className="small muted">PNG/JPG. Auto-resized to 256px.</div>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Details</h3>
          <div className="field">
            <label className="small muted">Display name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" maxLength={80} />
          </div>
          <div className="field">
            <label className="small muted">Email</label>
            <input value={user.email} disabled />
          </div>
          <div className="field">
            <label className="small muted">Member since</label>
            <input value={since} disabled />
          </div>
          <div className="account-save">
            <button className="btn" onClick={save} disabled={!dirty || busy}>
              {busy ? "Saving…" : "Save changes"}
            </button>
            <button className="btn ghost" onClick={onSignOut}>Sign out</button>
            {msg && <span className="small" style={{ color: msg.includes("✓") ? "var(--safe)" : "var(--crit)" }}>{msg}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
