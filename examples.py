from risk.board import Board,Territory
import copy

# define boards for the tests
# HINT: I recommend you plot these boards
board0 = Board([Territory(territory_id=i, player_id=1, armies=i%5+1) for i in range(42)])

board1 = copy.deepcopy(board0)
board1.set_owner(3,0)
board1.set_armies(3,500)
board1.set_armies(4,500)
board1.set_armies(34,500)
board1.set_armies(39,500)
board1.set_armies(35,500)


# board1.plot_board(path=path)



board2 = copy.deepcopy(board1)
board2.set_owner(34, 0)
board2.set_armies(34,1)
board2.set_owner(35, 0)
board2.set_armies(35,1)
board2.set_owner(39, 0)
board2.set_armies(39,1)
# board2.plot_board()
path=[39, 25, 35]
board2.plot_board(path=[25, 34, 21, 15, 31, 16, 38])



board3 = copy.deepcopy(board2)
board3.set_owner(34, 1)

board4 = copy.deepcopy(board2)
board4.set_owner(4, 0)
board4.set_armies(4, 1)
board4.set_owner(1, 0)


board5 = Board([Territory(territory_id=i, player_id=i%5, armies=i%4+1) for i in range(42)])
path=board5.cheapest_attack_path(3,18)
path=board5.cheapest_attack_path(3,6)

# board5.plot_board(path=[3, 4, 24, 8, 21, 0, 6])
# print("path=",path)
# board5.plot_board()
# board5.plot_board(path=[1,19])
#board5.plot_board(plot_graph=True,filename='board5_graph.png')
#board5.plot_board(plot_graph=False,filename='board5.png')
#board5.plot_board(plot_graph=True)
