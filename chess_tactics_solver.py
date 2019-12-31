import chess
import os
import numpy as np

piece_dict = { # Maps pieces to their values
'P':1,   # White pawn
'R':5,   # White rook
'N':3,   # White knight
'B':3,   # White bishop
'Q':9,   # White queen
'K':100, # White king
'.':0,   # Empty square
'p':-1,  # Black pawn
'r':-5,  # Black rook
'n':-3,  # Black knight
'b':-3,  # Black bishop
'q':-9,  # Black queen
'k':-100,# Black king
' ':0,   # Aesthetic buffer value in string translation
'\n':0,  # Similar to ^
}
position_table = {}


def mate_in_one(position):
    '''
    Accepts a given chess position where there is potentially a mate in one
    somewhere, and returns the move that delivers checkmate.  If no legal 
    move will deliver checkmate, then the None value is returned.
    '''
    correct_move = None
    # Iterate through all legal moves
    for move in position.legal_moves:
        # Make the move, and check to see if the position is checkmate
        position.push(move)
        if position.is_checkmate():
            # if it is, then set the correct move, undo the last move so
            # that the original position is present, and break out of the
            # loop.
            correct_move = move
            position.pop()
            break
        else:
            position.pop() # pop the last move if it's not checkmate.
    return correct_move

def mate_in_two(position):
    '''
    Accepts a chess position where there is potentially a mate in two
    somewhere, and returns the move that leads to checkmate.  If there is
    no such move, then None value is returned.
    '''
    correct_move = None
    for move1 in position.legal_moves:
        position.push(move1)
        broke = False # flag: becomes true if mate can be avoided
        for move2 in position.legal_moves:
            position.push(move2)
            if mate_in_one(position) is None:
                # If we reach a position where mate is avoided, then set
                # the broke flag to True, and try a new move1
                broke = True
                position.pop()
                break
            else:
                position.pop()
        if not broke:
            correct_move = move1
            position.pop()
            break
        else:
            position.pop()
    return correct_move

def simple_evaluate(position):
    '''
    Determines the value of the position by comparing piece value and
    nothing more.  A higher evaluation value translates to a higher
    advantage for white.
    '''
    global position_table
    boardfen = position.fen()
    if boardfen in position_table:
        return position_table[boardfen]

    r = position.result()
    if r == '1-0':
        #position_table[boardfen] = 9999
        return 9999 # White has won
    elif r == '0-1':
        #position_table[boardfen] = -9999
        return -9999 # Black has won
    elif r == '1/2-1/2':
        #position_table[boardfen] = 0
        return 0 # Draw, regardless of piece value (to avoid stalemates)
    board_val = 0
    for c in str(position):
        board_val += piece_dict[c]
    #position_table[boardfen] = board_val
    return board_val

#returns the next state
def Heuristic_AB(board,depth):
    global position_table
    position_table = {}
    count = 0
    if board.turn:
        v = Max_Value(board,-np.inf,np.inf,depth,count)
    else:
        v = Min_Value(board,-np.inf,np.inf,depth,count)
    position_table[board.fen()] = v
    for x in board.legal_moves:
        board.push(x)
        if (board.fen() in position_table and
        position_table[board.fen()]==v):
            board.pop()
            return x
        else:
            board.pop()

def Min_Value(board,a,b,depth,count):
    if cutoff_test(board,depth,count):
        v = simple_evaluate(board)
        position_table[board.fen()] = v
        return v
    v = np.inf
    for move in board.legal_moves:
        board.push(move)
        v = min(v, Max_Value(board,a,b,depth,count+0.5) )
        board.pop()
        if v <= a:
            position_table[board.fen()] = v
            return v
        b = min(b, v)
    position_table[board.fen()] = v
    return v

def Max_Value(board,a,b,depth,count):
    if cutoff_test(board,depth,count):
        v = simple_evaluate(board)
        position_table[board.fen()] = v
        return v
    v = -np.inf
    for move in board.legal_moves:
        board.push(move)
        v = max(v, Min_Value(board,a,b,depth,count+0.5) )
        board.pop()
        if v >= b:
            position_table[board.fen()] = v
            return v
        a = max(a, v)
    position_table[board.fen()] = v
    return v

def cutoff_test(board,depth,count):
    if count == depth: # If we're at the end of our search depth, stop
        return True
    if count % 1 == 0.5: # Never end on opponent's move
        return False
    if count == 0: # Consider the first position
        return False 
    current_evaluation = simple_evaluate(board)*(2*int(board.turn)-1)
    # currently, cutoff_value equals the advantage that the current player
    # has. Positions will be less likely to be searched if the player has a
    # strong advantage.
    net_potential = 0 # will aggregate the value of potential captures.
    for move in board.legal_moves:
        if board.is_capture(move):
            piece_val = board.piece_type_at(move.to_square)
            # queen = 5, rook = 4, bishop = 3, knight = 2, pawn = 1
            if piece_val == 1:
                net_potential += 1
            elif piece_val in [2,3]:
                net_potential += 3
            elif piece_val == 4:
                net_potential += 5
            elif piece_val == 5:
                net_potential += 9
        board.push(move)
        if board.is_check():
            net_potential += 6
        board.pop()
    # Higher net_potential will be more likely to be searched.
    distance_to_end = depth - count
    evaluation_weight = float(current_evaluation)/distance_to_end
    if evaluation_weight >= 1:
        return True
    potential_weight = net_potential * distance_to_end
    if potential_weight >= 15:
        return False
    return (net_potential + current_evaluation)*distance_to_end <= 10


def Solve(position, depth):
    move = mate_in_two(position)
    if not move is None:    #If there is a mate in two, just return the mate in two.
        return move         #If not, we're going to try some alpha beta stuff.
    else:
        move = Heuristic_AB(position,depth)
    position.push(move)
    if position_table[position.fen()] in [-1,0,1]:
        print("Probably not the ideal move here, by the way ... ")
    position.pop()
    return move

def noobPrint(board): #Adds numbers and letters to board. Not much here.
    fen = board.fen()
    index = 1
    nfen = ""
    for x in fen:
        if x == " ":
            break
        else:
            nfen += x
    nfen = nfen[::-1]

    for x in fen:
        if x.isdigit():
            for j in range(0,int(x)):
                print(". ",end="")
        elif x == "/":
            print("" + str(9-index))
            index+=1
        elif x == " ":
            break
        else:
            print(x,"",end="")
    print("" + str(9-index))
    print("a b c d e f g h")



def main():
    print("Remember, black pieces are lowercase and white pieces are capital")
    fen = input("Please enter a FEN: ")
    board = chess.Board(fen)
    print("INITIAL STATE: ")
    noobPrint(board)
    inp = " "
    cont = 0
    while(True):
        if cont % 2 == 0: #cont is for player turn. So, its always AI to move and then player.
            print("Thinking...")
            mov = Solve(board, 2)
            board.push(mov)
            print("Moving:",mov)
            noobPrint(board)
            input("Please press enter to continue.")
            os.system('cls' if os.name == 'nt' else 'clear')
        else:
            print("Please make a selection from the legal moves:")
            empty = 0
            for move in board.legal_moves: #print moves
                print(board.uci(move) + " ", end="")
                empty+=1
            print("")
            if empty == 0: #if there are no more moves, game over.
                print("no moves, game oger...")
                break
            empty = 0
            noobPrint(board)
            mov = input("\n")
            board.push(board.parse_uci(mov))
            input("\nPlease press enter to continue.")
            os.system('cls' if os.name == 'nt' else 'clear') #clears screen
        cont+=1
main()

# FENS that work:
# 8/7p/5Bp1/P4p2/q1p1rNk1/6P1/5P1P/5RK1 w - - 1 35 (mate)
# r7/5ppp/2k5/1p6/1Kp1b1P1/P1B4P/1P3P1R/4RB2 b - - 5 33 (mate)
# 1r1r2k1/p4p1p/3b2p1/1p1Q4/2p1B3/4P3/q1PP2PP/1N3RK1 w - - 2 21 (luck?)
# r1b3k1/1p3pp1/p7/3NP2r/8/P3K1RP/1P3p2/5R2 w - - 0 31 (tactic)
# 3r4/5pk1/p3p1p1/1p1bPq2/3R1P2/8/PP4P1/2QB2K1 w - - 1 30 (tactic, takes t)
