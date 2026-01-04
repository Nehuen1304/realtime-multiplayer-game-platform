import React from 'react';
import './SugerenciaAccion.css';

const SugerenciaAccion = ({ isVisible, instructionText }) => {
    return (
        <div className={`action-suggestion${!isVisible ? ' hidden' : ''}`}>
            <p>{instructionText}</p>
        </div>
    );
};

export default SugerenciaAccion;