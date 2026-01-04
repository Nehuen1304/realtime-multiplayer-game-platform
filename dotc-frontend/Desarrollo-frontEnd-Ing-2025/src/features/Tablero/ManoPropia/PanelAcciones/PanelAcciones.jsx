import React, { useState, useEffect, useMemo } from "react"
import { Button } from '../../../../components/Button/Button'
import './PanelAcciones.css'

// Panel de botones para las acciones del turno (descartar y pasar)
export function PanelAcciones({
    setPlayType,
    puedeFormarSet,
    puedeJugarEvento,
    puedeAgregarSet,
    socialDisgrace = false,
    onPassTurn,
    onDiscard,
    seJugo,
    manoLength,
    selectedCardsLength,
}) {
    
    // Controla si se puede pasar turno después de descartar
    const [puedePasarTurno, setPuedePasarTurno] = useState(null);
    // FAB (mobile)
    const [isFabOpen, setIsFabOpen] = useState(false);

    // Actualiza la configuracion de los botones cuando cambian las acciones disponibles
    // useEffect(() => {
    //     const discardAction = accion.find(action => action.type === 'DISCARD');
    //     const pasarTurnoAction = accion.find(action => action.type === 'PASAR_TURNO');

    //     if (discardAction) {
    //         setDescartarConfig({
    //             activa: discardAction.enabled,
    //             handler: discardAction.action,
    //             label: discardAction.label
    //         });
    //     }
    //     if (pasarTurnoAction) {
    //         setPasarTurnoConfig({
    //             activa: pasarTurnoAction.enabled,
    //             handler: pasarTurnoAction.action,
    //             label: pasarTurnoAction.label
    //         });
    //     } else {
    //         setDescartarConfig({ activa: false, handler: null, label: '' });
    //     }
    // }, [accion]);

    // helper para setPlayType que también habilita "Pasar turno"
    const handleSetPlayType = (type) => {
        if (typeof setPlayType === 'function') {
            setPlayType(type);
            setPuedePasarTurno(true);
        }
    };

    // Maneja el click en los botones de acción
    const handleActionClick = (type) => {
        if (type === 'DISCARD') {
            onDiscard();
            setPuedePasarTurno(true);
        }
        if (type === 'PASAR_TURNO') {
            onPassTurn();
        }
    };

    const closeFab = () => setIsFabOpen(false);
    const openFab = () => setIsFabOpen(true);

    // Lista unificada de acciones (para calcular cuántas están habilitadas)
    const actionDefs = useMemo(() => ([
        {
            key: 'DISCARD',
            enabled: selectedCardsLength > 0,
            label: 'DESCARTAR',
            onClick: () => handleActionClick('DISCARD'),
        },
        {
            key: 'PASAR_TURNO',
            enabled: seJugo && manoLength >= 6,
            label: 'PASAR',
            onClick: () => handleActionClick('PASAR_TURNO'),
        },
        {
            key: 'FORM_NEW_SET',
            enabled: puedeFormarSet && !socialDisgrace,
            label: 'Jugar Set',
            onClick: () => handleSetPlayType('FORM_NEW_SET'),
        },
        {
            key: 'ADD_TO_EXISTING_SET',
            enabled: puedeAgregarSet && !socialDisgrace,
            label: 'Añadir a Set',
            onClick: () => handleSetPlayType('ADD_TO_EXISTING_SET'),
        },
        {
            key: 'PLAY_EVENT',
            enabled: puedeJugarEvento && !socialDisgrace,
            label: 'Jugar Evento',
            onClick: () => handleSetPlayType('PLAY_EVENT'),
        },
    ]), [puedeFormarSet, puedeAgregarSet, puedeJugarEvento, socialDisgrace, onPassTurn, onDiscard, seJugo, manoLength, selectedCardsLength]);

    const enabledActions = useMemo(() => actionDefs.filter(a => a.enabled), [actionDefs]);

    // Si el sheet está abierto pero sólo queda 1 acción, cerrarlo y mostrar ese botón único
    useEffect(() => {
        if (isFabOpen && enabledActions.length === 1) {
            setIsFabOpen(false);
        }
    }, [isFabOpen, enabledActions]);

    return (
        <>
            {/* Desktop: panel horizontal */}
            <div className="panel-acciones-container">
                {actionDefs.map(action => (
                    <Button
                        key={action.key}
                        variant='small'
                        onClick={action.onClick}
                        disabled={!action.enabled}
                    >
                        {action.label}
                    </Button>
                ))}
            </div>

            {/* Mobile: FAB */}
            {!isFabOpen && enabledActions.length > 0 && (
                <div className="fab-container">
                    {enabledActions.length === 1 ? (
                        <Button
                            onClick={enabledActions[0].onClick}
                            variant="primary"
                            style={{ width: 'auto', height: 'auto', borderRadius: '8px', fontSize: '18px', padding: '12px 24px' }}
                        >
                            {enabledActions[0].label}
                        </Button>
                    ) : (
                        <Button
                            onClick={openFab}
                            variant="primary"
                            style={{ width: 'auto', height: 'auto', borderRadius: '8px', fontSize: '18px', padding: '12px 24px' }}
                        >
                            Opciones de turno
                        </Button>
                    )}
                </div>
            )}

            {isFabOpen && (
                <div className="fab-overlay" role="dialog" aria-modal="true" onClick={closeFab}>
                    <div className="fab-sheet" onClick={(e) => e.stopPropagation()}>
                        <div className="fab-sheet-header">
                            <span>Acciones de turno</span>
                            <button className="fab-close" aria-label="Cerrar" onClick={closeFab}>×</button>
                        </div>
                        <div className="fab-actions">
                            {enabledActions.map(action => (
                                <Button
                                    key={action.key}
                                    onClick={() => { action.onClick(); closeFab(); }}
                                    disabled={!action.enabled}
                                >
                                    {action.label}
                                </Button>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}