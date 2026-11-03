import { API_BASE as BASE_URL } from './config';
const API_BASE = `${BASE_URL}/api/v1`;

export async function incluirEstadoPatrones(tecnicas, token) {
  return Promise.all(tecnicas.map(async (tecnica) => {
    if (typeof tecnica.tiene_patron === 'boolean') return tecnica;

    try {
      const response = await fetch(`${API_BASE}/tecnicas/${tecnica.id}/patron`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const tienePatron = response.ok;
      return {
        ...tecnica,
        tiene_patron: tienePatron,
        tiene_video: tecnica.tiene_video || tienePatron,
      };
    } catch {
      return { ...tecnica, tiene_patron: false };
    }
  }));
}
