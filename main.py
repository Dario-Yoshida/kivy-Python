from kivy.app import App
from kivy.lang import Builder
from telas import *
from botoes import *
import requests
#quando utilizar requests em link http's', tem que utilizar o 'os' e 'certifi' abaixo
import os
import certifi
from bannervenda import BannerVenda
from functools import partial
from myfirebase import MyFirebase
from bannervendedor import BannerVendedor
from datetime import date

os.environ["SSL_CERT_FILE"] = certifi.where()

GUI = Builder.load_file("main.kv")
class MainApp(App):
    cliente = None
    produto = None
    unidade = None

    def build(self):
        self.firebase = MyFirebase()
        return GUI


    def on_start(self):
        #carregar fotos de perfil
        arquivo = os.listdir("icones/fotos_perfil")
        pagina_fotoperfil = self.root.ids["fotoperfilpage"]
        lista_fotos = pagina_fotoperfil.ids["lista_fotos_perfil"]
        for foto in arquivo:
            imagem = ImageButton(source=f"icones/fotos_perfil/{foto}", on_release=partial(self.mudar_foto_perfil, foto))
            lista_fotos.add_widget(imagem)

        #carregar fotos dos clientes
        arquivo = os.listdir("icones/fotos_clientes")
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarvendas.ids["lista_clientes"]
        for foto_cliente in arquivo:
            imagem = ImageButton(source=f"icones/fotos_clientes/{foto_cliente}",
                                 on_release=partial(self.selecionar_cliente, foto_cliente))
            label = LabelButton(text=foto_cliente.replace(".png", "").capitalize(),
                                on_release=partial(self.selecionar_cliente, foto_cliente))
            lista_clientes.add_widget(imagem)
            lista_clientes.add_widget(label)

        #carregar fotos dos produtos
        arquivo = os.listdir("icones/fotos_produtos")
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarvendas.ids["lista_produto"]
        for foto_produto in arquivo:
            imagem = ImageButton(source=f"icones/fotos_produtos/{foto_produto}",
                                 on_release=partial(self.selecionar_produto, foto_produto))
            label = LabelButton(text=foto_produto.replace(".png", "").capitalize(),
                                on_release=partial(self.selecionar_produto, foto_produto))
            lista_produtos.add_widget(imagem)
            lista_produtos.add_widget(label)

        #carregar data
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        label_data = pagina_adicionarvendas.ids["label_data"]
        label_data.text = f"Data: {date.today().strftime('%d/%m/%Y')}"

        #carrega infos do usuario
        self.carregar_infos_usuario()


    def carregar_infos_usuario(self):
        try:
            with open("refreshtoken.txt", "r") as arquivo:
                refresh_token = arquivo.read()
            local_id, id_token = self.firebase.trocar_token(refresh_token)
            self.local_id = local_id
            self.id_token = id_token

            #preenche dados vendedor
            requisicao = requests.get(f"https://kivypython-66261-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}")
            requisicao_dic = requisicao.json()

            #preenche foto perfil
            avatar = requisicao_dic['avatar']
            self.avatar = avatar
            foto_perfil = self.root.ids["foto_perfil"]
            foto_perfil.source = f"icones/fotos_perfil/{avatar}"

            # preencher ID unico vendedor
            id_vendedor = requisicao_dic['id_vendedor']
            self.id_vendedor = id_vendedor
            pagina_ajustes = self.root.ids["ajustepage"]
            pagina_ajustes.ids["id_vendedor"].text = f"O seu ID Único: {id_vendedor}"
            print(f"ID vendedor {id_vendedor}")

            #preencher total vendas
            total_vendas = requisicao_dic['total_vendas']
            self.total_vendas = total_vendas
            home_page = self.root.ids["homepage"]
            home_page.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

            #preencher equipe
            self.equipe = requisicao_dic["equipe"]

            #preenche dados da venda
            try:
                vendas = requisicao_dic["vendas"]
                self.vendas = vendas
                pagina_homepage = self.root.ids["homepage"]
                lista_vendas = pagina_homepage.ids["lista_vendas"]
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda["cliente"], foto_cliente=venda["foto_cliente"],
                        produto=venda["produto"], foto_produto=venda["foto_produto"], data=venda["data"],
                        quantidade=venda["quantidade"], preco=venda["preco"], unidade=venda["unidade"])
                    lista_vendas.add_widget(banner)
            except:
                pass

            #preencher lista vendedores
            equipe = requisicao_dic["equipe"]
            lista_equipe = equipe.split(",")
            pagina_listavendedores = self.root.ids["listarvendedorespage"]
            lista_vendedores = pagina_listavendedores.ids["lista_vendedores"]

            for id_vendedor_equipe in lista_equipe:
                if id_vendedor_equipe != "":
                    banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_equipe)
                    lista_vendedores.add_widget(banner_vendedor)


            self.mudar_tela("homepage")

        except:
            pass

    def mudar_tela(self, id_tela):
        gerenciador_tela = self.root.ids["screen_manager"]
        gerenciador_tela.current = id_tela

    def mudar_foto_perfil(self, foto, *args):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{foto}"

        info = f'{{"avatar": "{foto}"}}'
        requests.patch(f"https://kivypython-66261-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                                    data=info)
        self.mudar_tela("ajustepage")


    def adicionar_vendedor(self, id_vendedor_adicionado):
        link = f'https://kivypython-66261-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"&equalTo="{id_vendedor_adicionado}"'
        requisicao = requests.get(link)
        requisicao_dic = requisicao.json()

        pagina_adicionarvendedor = self.root.ids["adicionarvendedorpage"]
        mensagem_texto = pagina_adicionarvendedor.ids["mensagem_outrovendedor"]

        if requisicao_dic == {}:
            mensagem_texto.text = "Usuário não encontrado"
        else:
            equipe = self.equipe.split(",")
            if id_vendedor_adicionado in equipe:
                mensagem_texto.text = "Usuário ja faz parte da equipe"
            else:
                self.equipe = self.equipe + f",{id_vendedor_adicionado}"
                info = f'{{"equipe": "{self.equipe}"}}'
                requests.patch(f"https://kivypython-66261-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}", data=info)
                mensagem_texto.text = "Usuário adicionado com Sucesso"
                #adicionar novo banner com vendedor adicionado
                pagina_listavendedores = self.root.ids["listarvendedorespage"]
                lista_vendedores = pagina_listavendedores.ids["lista_vendedores"]
                banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_adicionado)
                lista_vendedores.add_widget(banner_vendedor)


    def selecionar_cliente(self, foto, *args):
        self.cliente = foto.replace(".png", "")
        #pintar todos de branco
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarvendas.ids["lista_clientes"]

        for item in list(lista_clientes.children):
            item.color = (1,1,1,1)
            # pintar de azul
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if texto == foto:
                    item.color = (0, 207/255, 219/255, 1)
            except:
                pass

    def selecionar_produto(self, foto, *args):
        self.produto = foto.replace(".png", "")
        # pintar todos de branco
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_produto = pagina_adicionarvendas.ids["lista_produto"]

        for item in list(lista_produto.children):
            item.color = (1, 1, 1, 1)
            # pintar de azul o item selecionado
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if texto == foto:
                    item.color = (0, 207 / 255, 219 / 255, 1)
            except:
                pass

    def selecionar_unidade(self, id_label, *args):
        self.unidade = id_label.replace("unidade_", "")
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]

        pagina_adicionarvendas.ids["unidade_kg"].color = (1,1,1,1)
        pagina_adicionarvendas.ids["unidade_unidades"].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids["unidade_litros"].color = (1, 1, 1, 1)

        pagina_adicionarvendas.ids[id_label].color = (0, 207 / 255, 219 / 255, 1)

    def adicionar_venda(self):
        produto = self.produto
        cliente = self.cliente
        unidade = self.unidade
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        data = pagina_adicionarvendas.ids["label_data"].text.replace("Data: ", "")
        preco = pagina_adicionarvendas.ids["preco_total"].text
        quantidade = pagina_adicionarvendas.ids["quantidade"].text

        if not cliente:
            pagina_adicionarvendas.ids["label_selecione_cliente"].color = (1,0,0,1)
        if not produto:
            pagina_adicionarvendas.ids["label_selecione_produto"].color = (1, 0, 0, 1)
        if not unidade:
            pagina_adicionarvendas.ids["unidade_kg"].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids["unidade_unidades"].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids["unidade_litros"].color = (1, 0, 0, 1)
        if not preco:
            pagina_adicionarvendas.ids["label_preco"].color = (1, 0, 0, 1)
        else:
            try:
                preco = float(preco)
            except:
                pagina_adicionarvendas.ids["label_preco"].color = (1, 0, 0, 1)
        if not quantidade:
            pagina_adicionarvendas.ids["label_quantidade"].color = (1, 0, 0, 1)
        else:
            try:
                quantidade = float(quantidade)
            except:
                pagina_adicionarvendas.ids["label_quantidade"].color = (1, 0, 0, 1)

        if produto and cliente and unidade and preco and quantidade and (type(preco)==float) and (type(quantidade)==float):
            foto_produto = produto + ".png"
            foto_cliente = cliente + ".png"

            info = f'{{"cliente": "{cliente}", "produto": "{produto}", "foto_cliente": "{foto_cliente}", ' \
                   f'"foto_produto": "{foto_produto}", "data": "{data}", "unidade": "{unidade}", ' \
                   f'"preco": "{preco}", "quantidade": "{quantidade}"}}'
            requests.post(f"https://kivypython-66261-default-rtdb.firebaseio.com/{self.local_id}/vendas.json?auth={self.id_token}", data=info)

            banner = BannerVenda(cliente=cliente, produto=produto, foto_cliente=foto_cliente, foto_produto=foto_produto,
                                 data=data, unidade=unidade, preco=preco, quantidade=quantidade)
            pagina_homepage = self.root.ids["homepage"]
            lista_vendas = pagina_homepage.ids["lista_vendas"]
            lista_vendas.add_widget(banner)

            requisicao = requests.get(f"https://kivypython-66261-default-rtdb.firebaseio.com/{self.local_id}/total_vendas.json?auth={self.id_token}")
            total_vendas = float(requisicao.json())
            total_vendas += preco
            info = f'{{"total_vendas": "{total_vendas}"}}'
            requests.patch(f"https://kivypython-66261-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}", data=info)
            #atualizar total_vendas
            home_page = self.root.ids["homepage"]
            home_page.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

            self.mudar_tela("homepage")

        self.produto = None
        self.cliente = None
        self.unidade = None

    def carregar_todas_vendas(self):
        pagina_todasvendas = self.root.ids["todasvendaspage"]
        lista_vendas = pagina_todasvendas.ids["lista_vendas"]

        #limpar o scroll anterior
        for item in list(lista_vendas.children):
            lista_vendas.remove_widget(item)

        # preenche dados da empresa
        requisicao = requests.get(f'https://kivypython-66261-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"')
        requisicao_dic = requisicao.json()

        # preenche foto perfil
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = "icones/fotos_perfil/hash.png"

        # preenche dados da venda
        total_vendas = 0
        for local_id_venda in requisicao_dic:
            try:
                vendas = requisicao_dic[local_id_venda]["vendas"]
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda["cliente"], foto_cliente=venda["foto_cliente"],
                                         produto=venda["produto"], foto_produto=venda["foto_produto"], data=venda["data"],
                                         quantidade=venda["quantidade"], preco=venda["preco"], unidade=venda["unidade"])
                    lista_vendas.add_widget(banner)
                    total_vendas += float(venda["preco"])
            except:
                pass
        label_total_vendas = pagina_todasvendas.ids["label_total_vendas"]
        label_total_vendas.text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"
        #redirecionar para todasvendaspage
        self.mudar_tela("todasvendaspage")


    def sair_todas_vendas(self, id_tela):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{self.avatar}"

        self.mudar_tela(id_tela)


    def carregar_vendas_vendedor(self, dic_info_vendedor, *args):


        try:

            vendas = dic_info_vendedor["vendas"]
            pagina_vendasoutrovendedor = self.root.ids["vendasoutrovendedorpage"]
            lista_vendas = pagina_vendasoutrovendedor.ids["lista_vendas"]

            # limpar o scroll anterior
            for item in list(lista_vendas.children):
                lista_vendas.remove_widget(item)

            for id_venda in vendas:
                venda = vendas[id_venda]
                banner = BannerVenda(cliente=venda["cliente"], foto_cliente=venda["foto_cliente"],
                                     produto=venda["produto"], foto_produto=venda["foto_produto"], data=venda["data"],
                                     quantidade=venda["quantidade"], preco=venda["preco"], unidade=venda["unidade"])
                lista_vendas.add_widget(banner)
        except:
            pass
        total_vendas = dic_info_vendedor["total_vendas"]
        pagina_vendasoutrovendedor.ids["label_total_vendas"].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

        # preenche foto perfil
        foto_perfil = self.root.ids["foto_perfil"]
        avatar = dic_info_vendedor["avatar"]
        foto_perfil.source = f'icones/fotos_perfil/{avatar}'

        self.mudar_tela("vendasoutrovendedorpage")
        

MainApp().run()

