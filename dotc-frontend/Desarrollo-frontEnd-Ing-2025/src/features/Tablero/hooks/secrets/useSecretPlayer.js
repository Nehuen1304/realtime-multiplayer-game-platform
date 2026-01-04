import { useCallback, useEffect, useState } from 'react';
import * as apiService from '../../ManoPropia/ManoPropiaService.js';

export const usePlayerSecret=({gameId, playerId})=>{
    const[secretP, setSecretP] = useState([]);
    const [cargando, setCargandoSecreto] = useState(false);
    const [errorSecreto, setErrorSecreto] = useState(null);

const secretPlayer = useCallback(async ()=>{
     if (!gameId || !playerId) return;
     setCargandoSecreto(true);
     setErrorSecreto(null);
     try {
         console.log("HABLANDO DESDE USESECRETOS");
        const responseSecreto = await apiService.getSecretosJugador(gameId,playerId);
        console.log("RESPUESTA SECRETOS:",responseSecreto);
        setSecretP(responseSecreto.secrets || []);
     } catch (e) {
        setErrorSecreto(e.message)
     }finally{
        setCargandoSecreto(false);
     }
    
},[gameId, playerId])
    useEffect(() => {
        secretPlayer();
    }, [secretPlayer]);

  return { secretP, setSecretP, cargando, errorSecreto, secretPlayer };
}