import random
import chess


def evaluate_board(board):
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            if piece.color == chess.WHITE:
                score += piece_values[piece.piece_type]
            else:
                score -= piece_values[piece.piece_type]
    return score


def minimax(board, depth, alpha, beta, white_to_play):
    best_score = -1000 if white_to_play else 1000
    if board.is_checkmate():
        return best_score
    if depth == 0:
        return evaluate_board(board)
    if white_to_play:
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if score > best_score:
                best_score = score
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
    else:
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if score < best_score:
                best_score = score
            beta = min(beta, best_score)
            if alpha >= beta:
                break
    return best_score


def get_move(board, depth):
    white_to_play = board.turn
    best_score = -1000 if white_to_play else 1000
    best_move = []
    for move in board.legal_moves:
        board.push(move)
        score = minimax(board, depth - 1, -10000, 10000, not white_to_play)
        board.pop()
        if score == best_score:
            best_move.append(move)
        elif score > best_score and white_to_play:
            best_score = score
            best_move = [move]
        elif score < best_score and not white_to_play:
            best_score = score
            best_move = [move]
    return random.choice(best_move)


piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 100
}
