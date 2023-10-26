```
# Загрузил код, отвещающий за прорисовку интерфейса, возможность игры с человеком и тд
import io
import chess.svg
import cairosvg
import pygame
import pygame.freetype
import bot
# from svglib.svglib import svg2rlg
# from reportlab.graphics import renderPM

BOARD_SIZE = 900
BORDER_SIZE = 34
SIDEBAR_SIZE = 200
SQUARE_LIGHT = "#D6DCE0"
SQUARE_DARK = "#7A909D"
SQUARE_SELECTED = "#5F707AFF"
SQUARE_MOVES = "#FFFFFFFF"
COLOR_INACTIVE = pygame.Color("lightskyblue3")
COLOR_ACTIVE = pygame.Color("dodgerblue2")


class Player:
    name = "Player"
    tag = 1


class Bot:
    depth = 3
    name = f"Bot (depth {depth})"
    tag = (bot.root, depth)


class ButtonBox:
    def __init__(self, x, y, w, h, text="", id=0):
        FONT = pygame.freetype.Font("terminus.ttf", 20)
        self.__rect = pygame.Rect(x, y, w, h)
        self.__color = COLOR_INACTIVE
        self.__text = text
        self.__id = id
        self.__txt_surface, self.__txt_rect = FONT.render(text, self.__color)
        self.__active = False

    def handle_event(self, event, app, board, player):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.__rect.collidepoint(event.pos):
                self.__active = not self.__active
                if self.__id == 1:
                    pygame.quit()
                    game = ChessApp(
                        player1=Player(),
                        player2=Player(),
                        color1=SQUARE_LIGHT,
                        color2=SQUARE_DARK,
                    )
                    game.play()
                if self.__id == 2:
                    pygame.quit()
                    game = ChessApp(
                        player1=Player(),
                        player2=Bot(),
                        color1=SQUARE_LIGHT,
                        color2=SQUARE_DARK,
                    )
                    game.play()
                if self.__id == 3 and len(app.logs) != 0:
                    if player == 1:
                        app.logs.pop(0)
                        board.pop()
                    else:
                        for x in range(2):
                            app.logs.pop(0)
                            board.pop()
            else:
                self.__active = False
            self.__color = COLOR_ACTIVE if self.__active else COLOR_INACTIVE

    def draw(self, screen):
        screen.blit(
            self.__txt_surface, (
                self.__rect.x + (self.__rect.w - self.__txt_rect.w) / 2,
                self.__rect.y + (self.__rect.h - self.__txt_rect.h) / 2,
            )
        )
        pygame.draw.rect(screen, self.__color, self.__rect, 2)


class ChessApp:
    def __init__(self, player1, player2, color1, color2):
        self.__board = chess.Board()

        pygame.init()
        pygame.display.set_caption(f"ChessApp: {player1.name} vs {player2.name}")
        self.__display = pygame.display.set_mode((BOARD_SIZE + SIDEBAR_SIZE, BOARD_SIZE))
        self.__display.fill((0, 0, 0))
        self.__clock = pygame.time.Clock()
        self.__player1 = player1.tag
        self.__player2 = player2.tag
        self.__color1 = color1
        self.__color2 = color2
        self.__gameOver = False
        self.__move_list = []
        self.__moves = []
        self.logs = []
        self.__button_boxes = []
        pygame.display.flip()

    def __get_board_style(self):
        colors = dict()
        colors['square light'] = self.__color1
        colors['square dark'] = self.__color2
        return colors

    def __render_list_moves(self, x, y):
        movesSurface = pygame.Surface((SIDEBAR_SIZE, BOARD_SIZE - y))
        movesSurface.fill((0, 0, 0))
        FONT = pygame.freetype.Font("terminus.ttf", 20)  # 17
        for i, l in enumerate(self.logs[0:17]):
            move_log, rect = FONT.render(l, (255, 255, 255))
            movesSurface.blit(
                move_log,
                (75, 0 + rect.h * i),
            )
        self.__display.blit(movesSurface, (BOARD_SIZE, y))

    def __get_sidebar(self):
        GAME_FONT = pygame.freetype.Font("terminus.ttf", 20)
        new_game, rect = GAME_FONT.render("New game", (255, 255, 255))
        self.__display.blit(
            new_game, (BOARD_SIZE + 60, 10)
        )
        game_or, rect = GAME_FONT.render("or", (255, 255, 255))
        self.__display.blit(
            game_or, (BOARD_SIZE + 90, 100)
        )
        game_moves, rect = GAME_FONT.render("Moves", (255, 255, 255))
        self.__display.blit(
            game_moves, (BOARD_SIZE + 70, 500)
        )
        self.__button_boxes = [
            ButtonBox(BOARD_SIZE + 10, 50, 180, 40, "Player VS Player", 1),
            ButtonBox(BOARD_SIZE + 10, 130, 180, 40, "Player VS Bot", 2),
            ButtonBox(BOARD_SIZE + 10, 440, 180, 40, "Redo last move", 3),
        ]
        for box in self.__button_boxes:
            box.draw(self.__display)
        self.__render_list_moves(BOARD_SIZE + 75, 540);
        pygame.display.flip()

    def __get_board_img(self, selected):
        if selected is not None:
            svg_board = chess.svg.board(
                board=self.__board,
                colors=self.__get_board_style(),
                fill=dict.fromkeys(self.__get_moves(selected), SQUARE_MOVES),
                size=BOARD_SIZE,
                style=f"""
                   rect.{chess.square_name(selected)} {{
                      fill: {SQUARE_SELECTED};
                   }}
                """,
            )
        else:
            svg_board = chess.svg.board(
                board=self.__board,
                colors=self.__get_board_style(),
                size=BOARD_SIZE,
            )

        png_io = io.BytesIO()
        cairosvg.svg2png(
            bytestring=bytes(svg_board, "utf8"),
            write_to=png_io
        )
        png_io.seek(0)

        # drawing = svg2rlg(svg_board)
        # renderPM.drawToFile(drawing, "board.png", fmt="PNG")

        surface = pygame.image.load(png_io, "png")
        return surface

    @staticmethod
    def __show_msg(self, text_surface):
        self.__display.blit(
            text_surface,
            text_surface.get_rect(center=(BOARD_SIZE / 2, BOARD_SIZE / 2))
        )
        pygame.display.flip()

    @staticmethod
    def __get_square(x, y):
        file = (x - BORDER_SIZE) // ((BOARD_SIZE - BORDER_SIZE * 2) // 8)
        rank = 8 - (y - BORDER_SIZE) // ((BOARD_SIZE - BORDER_SIZE * 2) // 8) - 1
        return file + rank * 8

    def __get_moves(self, square):
        moves = []
        for move in list(self.__board.legal_moves):
            move = str(move)
            start, dest = move[:2], move[2:4]
            if chess.square_name(square) == start:
                moves.append(chess.parse_square(dest))
        return moves

    def __player_make_move(self):
        if len(self.__move_list) == 2:  # Player clicked twice
            try:
                promotion_squares = [i for i in range(8)] if self.__board.turn == chess.BLACK else [i for i in
                                                                                                    range(56, 64)]
                if self.__move_list[1] in promotion_squares and self.__board.piece_at(
                        self.__move_list[0]).piece_type == chess.PAWN:
                    move = chess.Move(
                        from_square=self.__move_list[0],
                        to_square=self.__move_list[1],
                        promotion=chess.QUEEN
                    )
                else:
                    move = chess.Move(
                        from_square=self.__move_list[0],
                        to_square=self.__move_list[1]
                    )
                if move in self.__board.legal_moves:  # Move is legal
                    print(san := self.__board.san(move))
                    self.__moves.append(move)
                    self.__board.push_san(san)
                    self.logs.insert(0, str(move))
                else:  # Illegal move
                    raise chess.IllegalMoveError
            except chess.IllegalMoveError:
                pass
            except AttributeError:
                pass
            finally:
                self.__move_list = []

    def __computer_make_move(self):
        turn = self.__player1 if self.__board.turn else self.__player2
        move = turn[0](self.__board, turn[1])
        if move == chess.Move.null():
            move = list(self.__board.legal_moves)[-1]
        print(move)
        try:
            print(san := self.__board.san(move))
            self.__moves.append(san)
            self.logs.insert(0, str(move))
        except AssertionError:
            pass
        self.__board.push(move)

    def play(self):
        while True:
            self.__clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__gameOver = True
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.__gameOver = True
                        pygame.quit()
                        return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if pygame.mouse.get_pressed(3)[0]:
                        if BORDER_SIZE <= x <= BOARD_SIZE - BORDER_SIZE and BORDER_SIZE <= y <= BOARD_SIZE - BORDER_SIZE:
                            self.__move_list.append(self.__get_square(x, y))
                for box in self.__button_boxes:
                    box.handle_event(event, self, self.__board, self.__player2)

            if not self.__gameOver:  # If game is still ongoing
                if self.__board.turn:
                    self.__computer_make_move() if type(self.__player1) == tuple else self.__player_make_move()
                else:
                    self.__computer_make_move() if type(self.__player2) == tuple else self.__player_make_move()

            if not self.__gameOver:  # game is not over
                # Render board
                img = pygame.transform.scale(
                    self.__get_board_img(
                        None if not self.__move_list else self.__move_list[0]),
                    (BOARD_SIZE, BOARD_SIZE)
                )
                self.__display.blit(img, (0, 0))
                self.__get_sidebar()
                GAME_FONT = pygame.freetype.SysFont("terminus.ttf", 40)

                if self.__board.is_checkmate():  # Checkmate
                    text_surface, rect = GAME_FONT.render(
                        title := f"{'White' if not self.__board.turn else 'Black'} won the game by checkmate!",
                        (0, 0, 0)
                    )
                    self.__show_msg(self, text_surface);
                    pygame.display.set_caption(f"ChessApp: {title}")
                    self.__gameOver = True
                    print(self.__moves)

                if self.__board.is_stalemate():  # Stalemate
                    text_surface, rect = GAME_FONT.render(
                        title := "Draw by stalemate",
                        (0, 0, 0)
                    )
                    self.__show_msg(self, text_surface)
                    pygame.display.set_caption(f"ChessApp: {title}")
                    self.__gameOver = True
                    print(self.__moves)

                if self.__board.can_claim_draw():
                    text_surface, rect = GAME_FONT.render(
                        title := "Draw by threefold repetition",
                        (0, 0, 0)
                    )
                    self.__show_msg(self, text_surface)
                    pygame.display.set_caption(f"ChessApp: {title}")
                    self.__gameOver = True
                    print(self.__moves)

                if self.__board.is_insufficient_material():
                    text_surface, rect = GAME_FONT.render(
                        title := "Draw by insufficient material",
                        (0, 0, 0)
                    )
                    self.__show_msg(self, text_surface)
                    pygame.display.set_caption(f"ChessApp: {title}")
                    self.__gameOver = True
                    print(self.__moves)

                pygame.display.flip()


if __name__ in "__main__":
    game = ChessApp(
        player1=Player(),
        player2=Bot(),
        color1=SQUARE_LIGHT,
        color2=SQUARE_DARK,
    )
    game.play()
```
