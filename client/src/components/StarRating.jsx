// Componente reutilizable para mostrar estrellas de puntuacion
import { Star } from 'lucide-react';

export function StarRating({ score, size = 16, maxStars = 5 }) {
  return (
    <div className="flex">
      {Array.from({ length: maxStars }, (_, i) => (
        <Star
          key={`star-${i}`}
          size={size}
          className={i < score ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}
        />
      ))}
    </div>
  );
}

export default StarRating;
