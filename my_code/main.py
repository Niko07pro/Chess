import csv
import datetime
import io
import os
import platform
import subprocess
import time
import tkinter.filedialog

from cairosvg import svg2png
import chess.svg
import pygame
import pygame.freetype

import bot

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
    depth = 4
    name = f"Bot (depth {depth})"
    tag = (bot.get_move, depth)


class Bot2:
    depth = 3
    name = f"Bot (depth {depth})"
    tag = (bot.get_move, depth)


class ChessApp:
    def __init__(self, player1, player2, color1, color2):
        self.board = chess.Board()

        pygame.init()
        pygame.display.set_caption(f"ChessApp: {player1.name} vs {player2.name}")
        self.__display = pygame.display.set_mode((BOARD_SIZE + SIDEBAR_SIZE, BOARD_SIZE))
        self.__display.fill((0, 0, 0))
        self.__clock = pygame.time.Clock()
        self.player1 = player1
        self.player2 = player2
        self.__color1 = color1
        self.__color2 = color2
        self.__gameOver = False
        self.__move_list = []
        self.__moves = []
        self.logs = []
        self.__button_boxes = []
        self.__time = time.time()
        self.checkpoint = 0
        self.backInTime = False
        pygame.display.flip()

    def __set_stats(self, status):
        with open('stats.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([f"{self.player1.name} vs {self.player2.name}",
                             str(datetime.timedelta(seconds=time.time() - self.__time)), status])

    def __get_board_style(self):
        colors = dict()
        colors['square light'] = self.__color1
        colors['square dark'] = self.__color2
        return colors

    def __render_list_moves(self, y):
        movesSurface = pygame.Surface((SIDEBAR_SIZE, BOARD_SIZE - y))
        movesSurface.fill((0, 0, 0))
        FONT = pygame.freetype.Font('terminus.ttf', 20)
        for i, l in enumerate(list(reversed(self.logs[max(0, len(self.logs) - 10):len(self.logs)]))):
            move_log, rect = FONT.render(l, (255, 255, 255))
            movesSurface.blit(
                move_log,
                (75, rect.h * i),
            )
        self.__display.blit(movesSurface, (BOARD_SIZE, y))

    def __get_sidebar(self):
        GAME_FONT = pygame.freetype.Font("terminus.ttf", 25)  # "terminus.ttf"
        new_game, rect = GAME_FONT.render("New game", (255, 255, 255))
        self.__display.blit(
            new_game, (BOARD_SIZE + 50, 10)
        )
        game_moves, rect = GAME_FONT.render("Moves", (255, 255, 255))
        self.__display.blit(
            game_moves, (BOARD_SIZE + 60, 630)
        )
        self.__button_boxes = [
            ButtonBox(BOARD_SIZE + 10, 50, 180, 40, "Player VS Player", 1),
            ButtonBox(BOARD_SIZE + 10, 100, 180, 40, "Hard: White", 2),
            ButtonBox(BOARD_SIZE + 10, 150, 180, 40, "Hard: Black", 8),
            ButtonBox(BOARD_SIZE + 10, 200, 180, 40, "Easy: White", 9),
            ButtonBox(BOARD_SIZE + 10, 250, 180, 40, "Easy: Black", 10),
            ButtonBox(BOARD_SIZE + 10, 520, 180, 40, "Redo last move", 3),
            ButtonBox(BOARD_SIZE + 10, 420, 180, 40, "Statistics", 4),
            ButtonBox(BOARD_SIZE + 10, 470, 180, 40,
                      f"{'Checkpoint' if not self.backInTime else f'Back to {self.checkpoint} steps'}", 5),
            ButtonBox(BOARD_SIZE + 10, 320, 180, 40, "Save game", 6),
            ButtonBox(BOARD_SIZE + 10, 370, 180, 40, "Load game", 7),
            ButtonBox(BOARD_SIZE + 10, 570, 180, 40, "Give up", 11),
        ]
        for box in self.__button_boxes:
            box.draw(self.__display)
        self.__render_list_moves(670)
        pygame.display.flip()

    def __get_board_img(self, selected):
        if selected is not None:
            svg_board = chess.svg.board(
                board=self.board,
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
                board=self.board,
                colors=self.__get_board_style(),
                size=BOARD_SIZE,
            )

        png_io = io.BytesIO()
        svg2png(
            bytestring=bytes(svg_board, "utf8"),
            write_to=png_io
        )
        png_io.seek(0)

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
        for move in list(self.board.legal_moves):
            move = str(move)
            start, dest = move[:2], move[2:4]
            if chess.square_name(square) == start:
                moves.append(chess.parse_square(dest))
        return moves

    def __player_make_move(self):
        if len(self.__move_list) == 2:  # Player clicked twice
            try:
                promotion_squares = [i for i in range(8)] if self.board.turn == chess.BLACK else [i for i in
                                                                                                  range(56, 64)]
                if self.__move_list[1] in promotion_squares and self.board.piece_at(
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
                if move in self.board.legal_moves:  # Move is legal
                    san = self.board.san(move)
                    self.__moves.append(move)
                    self.board.push_san(san)
                    self.logs.append(str(move))
                    self.__increase_checkpoint()
                else:  # Illegal move
                    raise chess.IllegalMoveError
            except chess.IllegalMoveError:
                pass
            except AttributeError:
                pass
            finally:
                self.__move_list = []

    def __computer_make_move(self):
        turn = self.player1.tag if self.board.turn else self.player2.tag
        move = turn[0](self.board, turn[1])
        if move == chess.Move.null():
            move = list(self.board.legal_moves)[-1]
        try:
            san = self.board.san(move)
            self.__moves.append(san)
            self.logs.append(str(move))
        except AssertionError:
            pass
        self.board.push(move)
        self.__increase_checkpoint()

    def __increase_checkpoint(self):
        if self.backInTime:
            self.checkpoint += 1

    def __end_game(self, status, GAME_FONT):
        text_surface, rect = GAME_FONT.render(
            title := status,
            (0, 0, 0)
        )
        self.__show_msg(self, text_surface)
        pygame.display.set_caption(f"ChessApp: {title}")
        self.__gameOver = True
        self.__set_stats(status)

    def give_up(self):
        GAME_FONT = pygame.freetype.SysFont(None, 40)
        self.__end_game(f"{'White' if self.board.turn else 'Black'} lost the game by surrender", GAME_FONT)
        pygame.display.flip()

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
                        if BORDER_SIZE <= x <= BOARD_SIZE - BORDER_SIZE and \
                                BORDER_SIZE <= y <= BOARD_SIZE - BORDER_SIZE:
                            self.__move_list.append(self.__get_square(x, y))
                for box in self.__button_boxes:
                    box.handle_event(event)

            if not self.__gameOver:  # If game is still ongoing
                if self.board.turn:
                    self.__computer_make_move() if type(self.player1.tag) == tuple else self.__player_make_move()
                else:
                    self.__computer_make_move() if type(self.player2.tag) == tuple else self.__player_make_move()
                # Render board
                img = pygame.transform.scale(
                    self.__get_board_img(
                        None if not self.__move_list else self.__move_list[0]),
                    (BOARD_SIZE, BOARD_SIZE)
                )
                try:
                    self.__display.blit(img, (0, 0))
                    self.__get_sidebar()
                except pygame.error:
                    break
                GAME_FONT = pygame.freetype.SysFont(None, 40)
                if self.board.is_checkmate():  # Checkmate
                    self.__end_game(f"{'White' if not self.board.turn else 'Black'} won the game by checkmate!",
                                    GAME_FONT)

                if self.board.is_stalemate():  # Stalemate
                    self.__end_game("Draw by stalemate", GAME_FONT)

                if self.board.can_claim_draw():
                    self.__end_game("Draw by threefold repetition", GAME_FONT)

                if self.board.is_insufficient_material():
                    self.__end_game("Draw by insufficient material", GAME_FONT)

                pygame.display.flip()


class ButtonBox:
    def __init__(self, x, y, w, h, text="", id=0):
        FONT = pygame.freetype.Font(None, 20)
        self.__rect = pygame.Rect(x, y, w, h)
        self.__color = COLOR_INACTIVE
        self.__text = text
        self.__id = id
        self.__txt_surface, self.__txt_rect = FONT.render(text, self.__color)
        self.__active = False

    def handle_event(self, event):
        global game
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
                if self.__id == 3 and len(game.logs) != 0:
                    if game.player1.tag == game.player2.tag == 1:
                        game.logs.pop()
                        game.board.pop()
                    else:
                        for x in range(2):
                            game.logs.pop()
                            game.board.pop()
                if self.__id == 4:
                    filepath = os.path.realpath("stats.csv")
                    if platform.system() == "Darwin":  # macOS
                        subprocess.call(("open", filepath))
                    elif platform.system() == "Windows":  # Windows
                        os.startfile(filepath)
                    else:  # linux variants
                        subprocess.call(("xdg-open", filepath))
                if self.__id == 5 and len(game.logs) != 0:
                    if game.backInTime:
                        for x in range(game.checkpoint):
                            game.logs.pop()
                            game.board.pop()
                        game.checkpoint = 0
                        game.backInTime = False
                    else:
                        game.backInTime = True
                if self.__id == 6 and len(game.logs) != 0:
                    self.__save_file()
                if self.__id == 7:
                    self.__load_file()
                if self.__id == 8:
                    pygame.quit()
                    game = ChessApp(
                        player1=Bot(),
                        player2=Player(),
                        color1=SQUARE_LIGHT,
                        color2=SQUARE_DARK,
                    )
                    game.play()
                if self.__id == 9:
                    pygame.quit()
                    game = ChessApp(
                        player1=Player(),
                        player2=Bot2(),
                        color1=SQUARE_LIGHT,
                        color2=SQUARE_DARK,
                    )
                    game.play()
                if self.__id == 10:
                    pygame.quit()
                    game = ChessApp(
                        player1=Bot2(),
                        player2=Player(),
                        color1=SQUARE_LIGHT,
                        color2=SQUARE_DARK,
                    )
                    game.play()
                if self.__id == 11:
                    game.give_up()
            else:
                self.__active = False
            self.__color = COLOR_ACTIVE if self.__active else COLOR_INACTIVE

    def __load_file(self):
        global game
        top = tkinter.Tk()
        top.withdraw()
        file_name = tkinter.filedialog.askopenfilename(parent=top, filetypes=[("Text file", ".txt")])
        if file_name:
            file = open(file_name, "r")
            f = file.read()
            file.close()
            moves = f.split(' ')
            game = ChessApp(
                player1=Player(),
                player2=Bot(),
                color1=SQUARE_LIGHT,
                color2=SQUARE_DARK,
            )
            for m in moves:
                try:
                    move = chess.Move.from_uci(m)
                    if move in game.board.legal_moves:
                        san = game.board.san(move)
                        game.board.push_san(san)
                        game.logs.append(str(move))
                except chess.InvalidMoveError:
                    break
            game.play()
        top.destroy()

    def __save_file(self):
        global game
        b = ' '.join(game.logs)
        top = tkinter.Tk()
        top.withdraw()
        file_name = tkinter.filedialog.asksaveasfilename(parent=top, defaultextension='.txt',
                                                         filetypes=[("Text file", ".txt")])
        if file_name:
            file = open(file_name, 'w')
            file.write(b)
            file.close()
        top.destroy()

    def draw(self, screen):
        buttonSurface = pygame.Surface((self.__rect.w, self.__rect.h))
        buttonSurface.fill((0, 0, 0))
        screen.blit(buttonSurface, (self.__rect.x, self.__rect.y))
        screen.blit(
            self.__txt_surface, (
                self.__rect.x + (self.__rect.w - self.__txt_rect.w) / 2,
                self.__rect.y + (self.__rect.h - self.__txt_rect.h) / 2,
            )
        )
        pygame.draw.rect(screen, self.__color, self.__rect, 2)


if __name__ in "__main__":
    game = ChessApp(
        player1=Player(),
        player2=Bot(),
        color1=SQUARE_LIGHT,
        color2=SQUARE_DARK,
    )
    game.play()
